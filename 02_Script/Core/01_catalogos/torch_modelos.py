#
# Archivo: torch_modelos.py
# Autor: @Marcos Alejandro Collazos Marmolejo
#
# Modelos hechos a mano en PyTorch para que corran en GPU (scikit-learn no tiene
# backend CUDA). Cada clase respeta la interfaz de scikit-learn (fit / predict /
# transform / fit_predict + get_params/set_params via BaseEstimator), asi que
# encajan en el mismo flujo (clone, cross_val_predict, joblib) que el resto.
#
# El parametro `device` lo pasa el archivo de algoritmo con perfiles.device_torch()
# ("cuda:0", "cuda:1" o "cpu"); si CUDA no esta disponible se cae a CPU solo.
#
from __future__ import annotations

import numpy as np
import torch
from sklearn.base import (
    BaseEstimator, ClassifierMixin, ClusterMixin, OutlierMixin,
    RegressorMixin, TransformerMixin,
)
from sklearn.preprocessing import LabelEncoder

from .. import submodulo

config = submodulo("00_fundamentos.config")


def _resolver(device: str) -> torch.device:
    device = str(device)

    if device.startswith("cuda"):
        if not torch.cuda.is_available():
            raise RuntimeError(
                "Se solicitó GPU CUDA, pero PyTorch no tiene CUDA disponible.\n"
                f"PyTorch: {torch.__version__}\n"
                f"CUDA de PyTorch: {torch.version.cuda}\n"
                f"GPUs detectadas: {torch.cuda.device_count()}"
            )

        indice = 0
        if ":" in device:
            indice = int(device.split(":")[1])

        if indice >= torch.cuda.device_count():
            raise RuntimeError(
                f"Se solicitó {device}, pero solo existen "
                f"{torch.cuda.device_count()} GPU(s)."
            )

        return torch.device(device)

    return torch.device("cpu")



def _semilla() -> None:
    torch.manual_seed(config.SEMILLA)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(config.SEMILLA)


# Perceptron multicapa generico (capas_ocultas=() -> modelo lineal).
def _mlp(entrada: int, salida: int, capas_ocultas: tuple[int, ...]) -> torch.nn.Module:
    tam = [entrada, *capas_ocultas]
    modulos: list[torch.nn.Module] = []
    for a, b in zip(tam[:-1], tam[1:]):
        modulos += [torch.nn.Linear(a, b), torch.nn.ReLU()]
    modulos.append(torch.nn.Linear(tam[-1], salida))
    return torch.nn.Sequential(*modulos)


# Entrena una red con Adam sobre (X, y) en tensores. Devuelve la red entrenada.
def _entrenar(red, X, y, dispositivo, epocas, lr, perdida_fn):
    red = red.to(dispositivo)
    optimizador = torch.optim.Adam(red.parameters(), lr=lr, weight_decay=1e-4)
    Xt = torch.as_tensor(X, dtype=torch.float32, device=dispositivo)
    yt = torch.as_tensor(y, device=dispositivo)
    red.train()
    for _ in range(epocas):
        optimizador.zero_grad()
        perdida = perdida_fn(red(Xt), yt)
        perdida.backward()
        optimizador.step()
    red.eval()
    return red


# --- supervisado ------------------------------------------------------
class _RedSupervisada(BaseEstimator):
    def __init__(self, capas_ocultas=(128, 64), epocas=300, lr=1e-3, device="cpu"):
        self.capas_ocultas = tuple(capas_ocultas)
        self.epocas = epocas
        self.lr = lr
        self.device = device

    def __getstate__(self):
        estado = self.__dict__.copy()
        if estado.get("red_") is not None:
            estado["red_"] = estado["red_"].to("cpu")
        return estado

    def _pred_logits(self, X):
        disp = _resolver(self.device)
        red = self.red_.to(disp)
        with torch.no_grad():
            return red(torch.as_tensor(np.asarray(X), dtype=torch.float32, device=disp)).cpu().numpy()


# Clasificador MLP (softmax + entropia cruzada).
class MLPClasificador(_RedSupervisada, ClassifierMixin):
    def fit(self, X, y):
        _semilla()
        self._codificador = LabelEncoder().fit(y)
        y_cod = self._codificador.transform(y)
        self.classes_ = self._codificador.classes_
        X = np.asarray(X, dtype=np.float32)
        red = _mlp(X.shape[1], len(self.classes_), self.capas_ocultas)
        self.red_ = _entrenar(red, X, y_cod, _resolver(self.device),
                              self.epocas, self.lr, torch.nn.CrossEntropyLoss())
        return self

    def predict(self, X):
        return self._codificador.inverse_transform(self._pred_logits(X).argmax(axis=1))

    def predict_proba(self, X):
        return torch.softmax(torch.as_tensor(self._pred_logits(X)), dim=1).numpy()


# Regresor MLP (error cuadratico medio).
class MLPRegresor(_RedSupervisada, RegressorMixin):
    def fit(self, X, y):
        _semilla()
        X = np.asarray(X, dtype=np.float32)
        y = np.asarray(y, dtype=np.float32).reshape(-1, 1)
        red = _mlp(X.shape[1], 1, self.capas_ocultas)
        self.red_ = _entrenar(red, X, y, _resolver(self.device),
                              self.epocas, self.lr, torch.nn.MSELoss())
        return self

    def predict(self, X):
        return self._pred_logits(X).ravel()


# --- clustering ------------------------------------------------------
class KMeansTorch(BaseEstimator, ClusterMixin):
    def __init__(self, n_clusters=8, iteraciones=100, n_init=5, device="cpu"):
        self.n_clusters = n_clusters
        self.iteraciones = iteraciones
        self.n_init = n_init
        self.device = device

    def fit_predict(self, X, y=None):
        return self.fit(X).labels_

    # Inicializacion k-means++ (centros dispersos) con la semilla dada.
    def _init_kmeans_pp(self, datos, semilla):
        generador = torch.Generator(device="cpu").manual_seed(semilla)
        centros = [datos[int(torch.randint(len(datos), (1,), generator=generador))]]
        for _ in range(self.n_clusters - 1):
            d2 = torch.cdist(datos, torch.stack(centros)).min(dim=1).values ** 2
            idx = int(torch.multinomial((d2 / d2.sum()).cpu(), 1, generator=generador))
            centros.append(datos[idx])
        return torch.stack(centros)

    # Una corrida de Lloyd; devuelve (centros, asignacion, inercia).
    def _lloyd(self, datos, centros):
        asignacion = torch.zeros(len(datos), dtype=torch.long, device=datos.device)
        for _ in range(self.iteraciones):
            distancias = torch.cdist(datos, centros)
            asignacion = distancias.argmin(dim=1)
            nuevos = torch.stack([
                datos[asignacion == k].mean(dim=0) if (asignacion == k).any() else centros[k]
                for k in range(self.n_clusters)])
            if torch.allclose(nuevos, centros, atol=1e-5):
                centros = nuevos
                break
            centros = nuevos
        inercia = torch.cdist(datos, centros).min(dim=1).values.pow(2).sum().item()
        return centros, asignacion, inercia

    def fit(self, X, y=None):
        _semilla()
        disp = _resolver(self.device)
        datos = torch.as_tensor(np.asarray(X), dtype=torch.float32, device=disp)
        mejor = None
        for i in range(self.n_init):
            centros, asignacion, inercia = self._lloyd(
                datos, self._init_kmeans_pp(datos, config.SEMILLA + i))
            if mejor is None or inercia < mejor[2]:
                mejor = (centros, asignacion, inercia)
        self.cluster_centers_ = mejor[0].cpu().numpy()
        self.labels_ = mejor[1].cpu().numpy()
        self.inertia_ = mejor[2]
        return self

    def predict(self, X):
        disp = _resolver(self.device)
        datos = torch.as_tensor(np.asarray(X), dtype=torch.float32, device=disp)
        centros = torch.as_tensor(self.cluster_centers_, dtype=torch.float32, device=disp)
        return torch.cdist(datos, centros).argmin(dim=1).cpu().numpy()


# --- reduccion de dimensionalidad -----------------------------------
class PCATorch(BaseEstimator, TransformerMixin):
    def __init__(self, n_components=10, device="cpu"):
        self.n_components = n_components
        self.device = device

    def fit(self, X, y=None):
        disp = _resolver(self.device)
        datos = torch.as_tensor(np.asarray(X), dtype=torch.float32, device=disp)
        self._media = datos.mean(dim=0)
        centrado = datos - self._media
        U, S, Vh = torch.linalg.svd(centrado, full_matrices=False)
        k = self.n_components
        self.components_ = Vh[:k].cpu().numpy()
        var = (S ** 2) / (len(datos) - 1)
        self.explained_variance_ratio_ = (var[:k] / var.sum()).cpu().numpy()
        self.mean_ = self._media.cpu().numpy()
        return self

    def transform(self, X):
        disp = _resolver(self.device)
        datos = torch.as_tensor(np.asarray(X), dtype=torch.float32, device=disp)
        comp = torch.as_tensor(self.components_, dtype=torch.float32, device=disp)
        media = torch.as_tensor(self.mean_, dtype=torch.float32, device=disp)
        return ((datos - media) @ comp.T).cpu().numpy()

    def inverse_transform(self, Z):
        return np.asarray(Z) @ self.components_ + self.mean_


class _Autoencoder(BaseEstimator):
    def __init__(self, cuello=10, capas=(128,), epocas=300, lr=1e-3, device="cpu"):
        self.cuello = cuello
        self.capas = tuple(capas)
        self.epocas = epocas
        self.lr = lr
        self.device = device

    def __getstate__(self):
        estado = self.__dict__.copy()
        for clave in ("encoder_", "decoder_"):
            if estado.get(clave) is not None:
                estado[clave] = estado[clave].to("cpu")
        return estado

    def _ajustar(self, X):
        _semilla()
        disp = _resolver(self.device)
        X = np.asarray(X, dtype=np.float32)
        self.encoder_ = _mlp(X.shape[1], self.cuello, self.capas).to(disp)
        self.decoder_ = _mlp(self.cuello, X.shape[1], self.capas[::-1]).to(disp)
        parametros = list(self.encoder_.parameters()) + list(self.decoder_.parameters())
        optimizador = torch.optim.Adam(parametros, lr=self.lr)
        Xt = torch.as_tensor(X, device=disp)
        for _ in range(self.epocas):
            optimizador.zero_grad()
            perdida = torch.nn.functional.mse_loss(self.decoder_(self.encoder_(Xt)), Xt)
            perdida.backward()
            optimizador.step()
        self.encoder_.eval()
        self.decoder_.eval()

    def _errores(self, X):
        disp = _resolver(self.device)
        Xt = torch.as_tensor(np.asarray(X), dtype=torch.float32, device=disp)
        with torch.no_grad():
            recon = self.decoder_.to(disp)(self.encoder_.to(disp)(Xt))
            return ((recon - Xt) ** 2).mean(dim=1).cpu().numpy()


# Autoencoder como reductor de dimensionalidad (transform = cuello de botella).
class AutoencoderReductor(_Autoencoder, TransformerMixin):
    def fit(self, X, y=None):
        self._ajustar(X)
        return self

    def transform(self, X):
        disp = _resolver(self.device)
        Xt = torch.as_tensor(np.asarray(X), dtype=torch.float32, device=disp)
        with torch.no_grad():
            return self.encoder_.to(disp)(Xt).cpu().numpy()

    def inverse_transform(self, Z):
        disp = _resolver(self.device)
        Zt = torch.as_tensor(np.asarray(Z), dtype=torch.float32, device=disp)
        with torch.no_grad():
            return self.decoder_.to(disp)(Zt).cpu().numpy()


# Autoencoder como detector de anomalias (error de reconstruccion alto = anomalia).
class AutoencoderAnomalias(_Autoencoder, OutlierMixin):
    def __init__(self, cuello=10, capas=(128,), epocas=300, lr=1e-3,
                 contaminacion=0.05, device="cpu"):
        super().__init__(cuello, capas, epocas, lr, device)
        self.contaminacion = contaminacion

    def fit(self, X, y=None):
        self._ajustar(X)
        self._umbral = float(np.quantile(self._errores(X), 1 - self.contaminacion))
        return self

    def fit_predict(self, X, y=None):
        return self.fit(X).predict(X)

    def predict(self, X):
        return np.where(self._errores(X) > self._umbral, -1, 1)

    def score_samples(self, X):
        return -self._errores(X)

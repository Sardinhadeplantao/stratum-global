"""Eventos com lugar no mapa (decisão 0014). Hoje: terremotos do Serviço Geológico dos EUA (USGS), feed público sem
chave, magnitude 4,5 ou mais nas últimas 24 horas. Devolvem eventos; quem grava é o robô."""
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone

TEMPO_LIMITE = 30


@dataclass(frozen=True)
class Evento:
    ext_id: str              # o código do evento na fonte
    versao: str              # muda quando a fonte revisa o evento (hora da atualização)
    titulo: str
    url: str | None
    magnitude: float | None
    lat: float
    lon: float
    ocorreu_em: datetime     # UTC, sem fuso


def _hora(ms) -> datetime:
    return datetime.fromtimestamp(ms / 1000, timezone.utc).replace(tzinfo=None)


def interpretar_usgs(texto: str) -> list[Evento]:
    """GeoJSON do USGS: cada terremoto com id, propriedades (title, mag, time, updated, url) e o ponto (lon, lat)."""
    try:
        dados = json.loads(texto)
    except ValueError:
        raise ValueError("formato inesperado: a resposta não é JSON") from None
    if not isinstance(dados, dict) or dados.get("type") != "FeatureCollection":
        raise ValueError("formato inesperado: não é uma coleção de terremotos")
    saida = []
    for f in dados.get("features") or []:
        try:
            p, (lon, lat) = f["properties"], f["geometry"]["coordinates"][:2]
            evento = Evento(str(f["id"]), str(p["updated"]), str(p["title"]),
                            p["url"] if str(p.get("url") or "").startswith("https://") else None,
                            float(p["mag"]) if p.get("mag") is not None else None,
                            float(lat), float(lon), _hora(p["time"]))
        except (KeyError, TypeError, ValueError):
            raise ValueError(f"formato inesperado: terremoto {str(f.get('id'))[:20]!r} sem os campos esperados") from None
        if not (math.isfinite(evento.lat) and math.isfinite(evento.lon) and -90 <= evento.lat <= 90
                and -180 <= evento.lon <= 180):
            raise ValueError(f"valor ilegível em {evento.ext_id}: coordenadas fora do mapa")
        saida.append(evento)
    return saida


def ler_usgs(fonte: dict, session, user_agent: str) -> list[Evento]:
    r = session.get(fonte["url"], headers={"User-Agent": user_agent, "Accept": "application/geo+json, application/json"},
                    timeout=TEMPO_LIMITE)
    if r.status_code >= 400:
        raise RuntimeError(f"HTTP {r.status_code}")
    return interpretar_usgs(r.content.decode("utf-8"))


CONECTORES = {"usgs": ler_usgs}

"""Saved profiles manager: in-memory list helpers, JSON export/import, optional local-file persistence."""
import json
import os
from typing import Any, Dict, List

PROFILES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".saved_profiles.json")

DEFAULT_PROFILES: List[Dict[str, Any]] = [
    {"name": "範例：命盤主 A", "date": "1990/01/01", "time": "12:00", "city": "台北市", "lat": 25.03, "lon": 121.50, "tz": 8.0},
    {"name": "範例：合盤對象 B", "date": "1992/06/15", "time": "12:00", "city": "台北市", "lat": 25.03, "lon": 121.50, "tz": 8.0},
]


class ProfilesManager:
    @staticmethod
    def default_profiles() -> List[Dict[str, Any]]:
        return [dict(p) for p in DEFAULT_PROFILES]

    @staticmethod
    def _clean(p: Any) -> Dict[str, Any]:
        if not isinstance(p, dict) or not str(p.get("name", "")).strip():
            raise ValueError("invalid profile")
        return {"name": str(p["name"]).strip(), "date": str(p.get("date", "")), "time": str(p.get("time", "")),
                "city": str(p.get("city", "")), "lat": float(p.get("lat", 25.03)),
                "lon": float(p.get("lon", 121.50)), "tz": float(p.get("tz", 8.0))}

    @staticmethod
    def save_profile(profiles_list, name, date_str, time_str, city, lat, lon, tz) -> List[Dict[str, Any]]:
        new = ProfilesManager._clean({"name": name, "date": date_str, "time": time_str, "city": city,
                                      "lat": lat, "lon": lon, "tz": tz})
        out = [dict(p) for p in profiles_list or []]
        for i, p in enumerate(out):
            if p.get("name") == new["name"]:
                out[i] = new
                return out
        out.append(new)
        return out

    @staticmethod
    def delete_profile(profiles_list, name) -> List[Dict[str, Any]]:
        return [dict(p) for p in profiles_list or [] if p.get("name") != name]

    @staticmethod
    def export_profiles_json(profiles_list) -> str:
        return json.dumps(list(profiles_list or []), ensure_ascii=False, indent=2)

    @staticmethod
    def import_profiles_json(existing_list, json_str) -> List[Dict[str, Any]]:
        """Merge profiles from JSON (by name, imported wins). Raises ValueError on malformed input."""
        try:
            data = json.loads(json_str)
        except (TypeError, ValueError) as e:
            raise ValueError(f"JSON 格式錯誤: {e}")
        if isinstance(data, dict):
            data = data.get("profiles", [data])
        if not isinstance(data, list):
            raise ValueError("JSON 必須為書籤陣列")
        out = [dict(p) for p in existing_list or []]
        for raw in data:
            p = ProfilesManager._clean(raw)
            for i, q in enumerate(out):
                if q.get("name") == p["name"]:
                    out[i] = p
                    break
            else:
                out.append(p)
        return out

    @staticmethod
    def load_from_file(path: str = PROFILES_FILE) -> List[Dict[str, Any]]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return ProfilesManager.import_profiles_json([], f.read())
        except Exception:
            return ProfilesManager.default_profiles()

    @staticmethod
    def save_to_file(profiles_list, path: str = PROFILES_FILE) -> bool:
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(ProfilesManager.export_profiles_json(profiles_list))
            return True
        except Exception:
            return False

#!/usr/bin/env python3
"""
Aggregates raw responses from Windsor.ai (Google Ads + GA4) and SE Ranking
into the snapshot.json schema consumed by the Vercel dashboard.

Usage:
  python3 aggregate.py <ads_file> <ga_file> <seo_file> <output_path> [today_iso]

Each input file is the JSON response saved by the MCP tool (with shape
{"result": [...]}  for Windsor.ai, {"data": [...]} for SE Ranking).
"""
import json
import sys
import unicodedata
from datetime import datetime

CAMPAIGN_MAP = {
    "Análises Laboratoriais": "ANA",
    "Caixa D'água e Reservatórios": "HDR",
    "Análise de Ar": "AR",
    "Análise de Efluentes": "EFLUENTES",
}

CHANNEL_MAP = {
    "Organic Search": "Organic Search",
    "Direct": "Direct",
    "Paid Search": "Paid Search",
    "Unassigned": "Não atribuído",
    "Email": "Email",
    "Referral": "Outros sites/Referência",
    "Organic Social": "Organic Social",
    "Organic Video": "Organic Video",
}

TARGET_KEYWORDS = [
    "análise de água",
    "análise de ar",
    "análise de efluentes",
    "limpeza de caixa d'água",
]


def norm(s: str) -> str:
    s = (s or "").lower()
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").strip()


def aggregate_ads(rows):
    out = {}
    for r in rows:
        date = r.get("date", "")
        if len(date) < 10:
            continue
        y = int(date[:4])
        m = int(date[5:7])
        camp = CAMPAIGN_MAP.get(r.get("campaign"), r.get("campaign"))
        out.setdefault(y, {}).setdefault(m, {}).setdefault(camp, {"clicks": 0, "cost": 0, "conv": 0, "impr": 0})
        bucket = out[y][m][camp]
        bucket["clicks"] += r.get("clicks", 0) or 0
        bucket["cost"] += r.get("cost", 0) or 0
        bucket["conv"] += r.get("conversions", 0) or 0
        bucket["impr"] += r.get("impressions", 0) or 0
    return out


def aggregate_ga(rows):
    out = {}
    for r in rows:
        date = r.get("date", "")
        if len(date) < 10:
            continue
        y = int(date[:4])
        m = int(date[5:7])
        ch = CHANNEL_MAP.get(r.get("default_channel_group"), r.get("default_channel_group"))
        out.setdefault(y, {}).setdefault(m, {}).setdefault(ch, 0)
        out[y][m][ch] += r.get("sessions", 0) or 0
    return out


def latest_seo_positions(engines):
    results = []
    for tkw in TARGET_KEYWORDS:
        target = norm(tkw)
        best = None
        for eng in engines or []:
            for kw in eng.get("keywords", []) or []:
                if norm(kw.get("name", "")) != target:
                    continue
                positions = kw.get("positions") or []
                sp = sorted(positions, key=lambda p: p.get("date", ""), reverse=True)
                if not sp:
                    continue
                latest = sp[0]
                cand = {
                    "name": kw.get("name"),
                    "pos": latest.get("pos"),
                    "change": latest.get("change", 0),
                    "date": latest.get("date"),
                    "volume": kw.get("volume", 0),
                }
                if best is None:
                    best = cand
                    continue
                cand_ranked = (cand["pos"] or 0) > 0
                best_ranked = (best["pos"] or 0) > 0
                if cand_ranked and not best_ranked:
                    best = cand
                elif cand_ranked and best_ranked and cand["pos"] < best["pos"]:
                    best = cand
        if best is None:
            best = {"name": tkw, "pos": None, "change": 0, "date": None, "volume": 0}
        results.append(best)
    return results


def main():
    if len(sys.argv) < 5:
        print("Usage: aggregate.py <ads_file> <ga_file> <seo_file> <output_path> [today_iso]", file=sys.stderr)
        sys.exit(2)
    ads_path, ga_path, seo_path, out_path = sys.argv[1:5]
    today = sys.argv[5] if len(sys.argv) > 5 else datetime.now().strftime("%Y-%m-%d")

    with open(ads_path) as f:
        ads = json.load(f).get("result", [])
    with open(ga_path) as f:
        ga = json.load(f).get("result", [])
    with open(seo_path) as f:
        seo = json.load(f).get("data", [])

    snapshot = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "today": today,
        "ads_ym": aggregate_ads(ads),
        "ga_ym": aggregate_ga(ga),
        "seo": latest_seo_positions(seo),
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False)

    print(f"snapshot written: {out_path} (ads_rows={len(ads)} ga_rows={len(ga)} seo_engines={len(seo)})")


if __name__ == "__main__":
    main()

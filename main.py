import os
import csv
import time
import requests

ODDS_API_KEY = os.getenv("ODDS_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT = os.getenv("TELEGRAM_CHAT_ID")

CASAS_AUTORIZADAS = ["Pinnacle", "Bet365", "Betano", "Superbet", "Betfair"]

def enviar_alerta(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT, "text": msg})

def calcular_ev(odd_justa, odd_atual):
    prob_real = 1 / odd_justa
    return round((odd_atual * prob_real) - 1, 4)

def monitorar():
    while True:
        with open("apostas.csv", newline="", encoding="utf-8") as f:
            apostas = csv.DictReader(f)
            for row in apostas:
                jogo = row["jogo"]
                mercado = row["mercado"]
                selecao = row["selecao"]
                odd_justa = float(row["odd_justa"])
                ev_min = float(row["ev_minimo"])

                time1, time2 = jogo.split(" x ")
                try:
                    url = "https://api.the-odds-api.com/v4/sports/soccer_league_of_ireland/odds"
                    params = {
                        "apiKey": ODDS_API_KEY,
                        "regions": "eu",
                        "markets": ",".join(["h2h", "double_chance", "totals"]),
                        "oddsFormat": "decimal"
                    }
                    resp = requests.get(url, params=params)
                    print(f"Status Code: {resp.status_code}")
                    print(f"Resposta API (primeiros 500 chars): {resp.text[:500]}")

                    if resp.status_code != 200:
                        print("Erro na requisição da API, status diferente de 200.")
                        continue

                    eventos = resp.json()

                    for evento in eventos:
                        home = evento["home_team"]
                        away = evento["away_team"]
                        if time1 in (home, away) and time2 in (home, away):
                            for bookmaker in evento["bookmakers"]:
                                nome_casa = bookmaker["title"]
                                if nome_casa not in CASAS_AUTORIZADAS:
                                    continue
                                for market in bookmaker["markets"]:
                                    if market["key"] != mercado:
                                        continue
                                    for outcome in market["outcomes"]:
                                        nome_outcome = outcome.get("name", "")
                                        label = ""
                                        if mercado == "totals":
                                            if outcome.get("point") != 2.5:
                                                continue
                                            label = f"{outcome['name']} 2.5"
                                        else:
                                            label = nome_outcome
                                        if label.lower() == selecao.lower():
                                            odd_atual = outcome["price"]
                                            ev = calcular_ev(odd_justa, odd_atual)
                                            if ev >= ev_min:
                                                mensagem = (
                                                    f"📢 Oportunidade de aposta!\n"
                                                    f"🏟️ Jogo: {jogo}\n"
                                                    f"🎯 Mercado: {mercado}\n"
                                                    f"🎯 Seleção: {selecao}\n"
                                                    f"💰 Odd Atual: {odd_atual} ({nome_casa})\n"
                                                    f"🎯 Odd Justa: {odd_justa}\n"
                                                    f"📈 EV: {round(ev*100, 2)}%"
                                                )
                                                enviar_alerta(mensagem)
                except Exception as e:
                    print(f"Erro ao buscar odds: {e}")
        time.sleep(300)

if __name__ == "__main__":
    monitorar()


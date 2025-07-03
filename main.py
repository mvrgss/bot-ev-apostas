import os
import csv
import time
import requests
from oddsapi import OddsApiClient

ODDS_API_KEY = os.getenv("ODDS_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT = os.getenv("TELEGRAM_CHAT_ID")

client = OddsApiClient(api_key=ODDS_API_KEY)

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
                mercado = row.get("mercado", "")
                odd_justa = float(row["odd_justa"])
                ev_min = float(row["ev_minimo"])

                # Aqui simplificado: buscamos odds da Pinnacle para o esporte futebol inglês (soccer_epl)
                # Você pode alterar 'soccer_epl' para o esporte da sua preferência
                try:
                    resp = client.sports_odds(sport="soccer_epl", region="eu", markets=["totals", "h2h"])
                    for evento in resp.data:
                        if jogo.split(" x ")[0] in (evento.home_team, evento.away_team) or jogo.split(" x ")[1] in (evento.home_team, evento.away_team):
                            for bookmaker in evento.bookmakers:
                                for market in bookmaker.markets:
                                    for outcome in market.outcomes:
                                        odd_atual = outcome.price
                                        ev = calcular_ev(odd_justa, odd_atual)
                                        if ev >= ev_min:
                                            mensagem = (
                                                f"📢 Oportunidade de aposta!\n"
                                                f"Jogo: {jogo}\n"
                                                f"Mercado: {mercado}\n"
                                                f"Odd Atual: {odd_atual}\n"
                                                f"Odd Justa: {odd_justa}\n"
                                                f"EV: {round(ev*100, 2)}%"
                                            )
                                            enviar_alerta(mensagem)
                except Exception as e:
                    print(f"Erro ao buscar odds: {e}")
        time.sleep(300)  # Espera 5 minutos antes de rodar novamente

if __name__ == "__main__":
    monitorar()

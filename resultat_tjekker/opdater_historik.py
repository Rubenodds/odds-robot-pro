import sqlite3
import datetime
import re
import sys
import os

# Sikrer at Python altid kan se mappen, uanset hvordan Streamlit kalder den
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import match_stats_api
except ImportError:
    from resultat_tjekker import match_stats_api

from historik import gem_data

def evaluer_enkelt_forslag(forslag_tekst, stats):
    """
    Intelligent tekst-scanner, der tolker forslaget og sammenligner 
    med de rå data fra API-motoren (indkast, frispark, offsides, mål, hjørner, kort, skud).
    Returnerer True hvis spillet er vundet, ellers False.
    """
    if not stats or not stats.get("match_found"):
        return False
        
    tekst = forslag_tekst.lower()
    
    # 1. INDKAST MARKEDER
    if "indkast" in tekst:
        tal_match = re.search(r'over\s+(\d+\.\d+|\d+)', tekst)
        if tal_match:
            graense = float(tal_match.group(1))
            samlet_indkast = stats.get("indkast_hj", 0) + stats.get("indkast_ud", 0)
            if "hj" in tekst or "hjemme" in tekst:
                return stats.get("indkast_hj", 0) > graense
            elif "ud" in tekst or "ude" in tekst:
                return stats.get("indkast_ud", 0) > graense
            return samlet_indkast > graense
        if "flest indkast til ude" in tekst or "flest indkast til ud" in tekst:
            return stats.get("indkast_ud", 0) > stats.get("indkast_hj", 0)
        if "flest indkast til hjemme" in tekst or "flest indkast til hj" in tekst:
            return stats.get("indkast_hj", 0) > stats.get("indkast_ud", 0)

    # 2. FRISPARK MARKEDER
    if "frispark" in tekst:
        tal_match = re.search(r'over\s+(\d+\.\d+|\d+)', tekst)
        if tal_match:
            graense = float(tal_match.group(1))
            samlet_fri = stats.get("frispark_begaaet_hj", 0) + stats.get("frispark_begaaet_ud", 0)
            if "hj" in tekst or "hjemme" in tekst:
                return stats.get("frispark_begaaet_hj", 0) > graense
            elif "ud" in tekst or "ude" in tekst:
                return stats.get("frispark_begaaet_ud", 0) > graense
            return samlet_fri > graense
        if "flest frispark" in tekst and ("ude" in tekst or "ud" in tekst):
            return stats.get("frispark_begaaet_ud", 0) > stats.get("frispark_begaaet_hj", 0)
        if "flest frispark" in tekst and ("hjemme" in tekst or "hj" in tekst):
            return stats.get("frispark_begaaet_hj", 0) > stats.get("frispark_begaaet_ud", 0)

    # 3. OFFSIDES MARKEDER
    if "offsides" in tekst or "offside" in tekst:
        tal_match = re.search(r'over\s+(\d+\.\d+|\d+)', tekst)
        if tal_match:
            graense = float(tal_match.group(1))
            samlet_off = stats.get("offsides_hj", 0) + stats.get("offsides_ud", 0)
            if "hj" in tekst or "hjemme" in tekst:
                return stats.get("offsides_hj", 0) > graense
            elif "ud" in tekst or "ude" in tekst:
                return stats.get("offsides_ud", 0) > graense
            return samlet_off > graense

    # 4. HJØRNESPARK MARKEDER
    if "hjørnespark" in tekst or "hjørne" in tekst:
        tal_match = re.search(r'over\s+(\d+\.\d+|\d+)', tekst)
        if tal_match:
            graense = float(tal_match.group(1))
            samlet_hjo = stats.get("hjoerne_hj", 0) + stats.get("hjoerne_ud", 0)
            if "hj" in tekst or "hjemme" in tekst:
                return stats.get("hjoerne_hj", 0) > graense
            return samlet_hjo > graense
        if "flest hjørnespark til" in tekst:
            return stats.get("hjoerne_hj", 0) > stats.get("hjoerne_ud", 0)

    # 5. MÅL & KAMPVINDER MARKEDER
    if "vinder" in tekst or "resultat:" in tekst:
        if "hj" in tekst or "hjemme" in tekst:
            return stats.get("maal_hj", 0) > stats.get("maal_ud", 0)
        elif "ud" in tekst or "ude" in tekst:
            return stats.get("maal_ud", 0) > stats.get("maal_hj", 0)
    if "begge hold scorer" in tekst:
        return stats.get("maal_hj", 0) > 0 and stats.get("maal_ud", 0) > 0
    if "mål i kampen" in tekst and "over" in tekst:
        tal_match = re.search(r'over\s+(\d+\.\d+|\d+)', tekst)
        if tal_match:
            return (stats.get("maal_hj", 0) + stats.get("maal_ud", 0)) > float(tal_match.group(1))

    # 6. TACKLINGER MARKEDER
    if "tacklinger" in tekst or "tackling" in tekst:
        tal_match = re.search(r'over\s+(\d+\.\d+|\d+)', tekst)
        if tal_match:
            graense = float(tal_match.group(1))
            samlet_tac = stats.get("tacklinger_hj", 0) + stats.get("tacklinger_ud", 0)
            if "hj" in tekst or "hjemme" in tekst:
                return stats.get("tacklinger_hj", 0) > graense
            elif "ud" in tekst or "ude" in tekst:
                return stats.get("tacklinger_ud", 0) > graense
            return samlet_tac > graense

    # 7. KORT MARKEDER (GULE/RØDE)
    if "kort" in tekst:
        tal_match = re.search(r'over\s+(\d+\.\d+|\d+)', tekst)
        if tal_match:
            graense = float(tal_match.group(1))
            samlet_kort = stats.get("kort_gule_hj", 0) + stats.get("kort_gule_ud", 0) + stats.get("kort_roede_hj", 0) + stats.get("kort_roede_ud", 0)
            if "hj" in tekst or "hjemme" in tekst:
                return (stats.get("kort_gule_hj", 0) + stats.get("kort_roede_hj", 0)) > graense
            elif "ud" in tekst or "ude" in tekst:
                return (stats.get("kort_gule_ud", 0) + stats.get("kort_roede_ud", 0)) > graense
            return samlet_kort > graense

    return True

def afgoer_alle_afventende_kuponer_live():
    """
    Hovedmotor: Læser SQLite-databasen, skiller kuponerne ad, kalder API og gemmer afgørelsen.
    """
    try:
        conn = sqlite3.connect("odds_pro_hukommelse.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, dato, ligaer, forslag FROM kupon_historik WHERE status = 'Afventer'")
        kuponer = cursor.fetchall()
        
        if not kuponer:
            conn.close()
            return
            
        nu_dato = (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).date()
        database_opdateret = False
        
        for kupon in kuponer:
            kupon_id, kupon_dato_str, ligaer_str, forslag_str = kupon
            kupon_dato = datetime.datetime.strptime(kupon_dato_str, "%Y-%m-%d").date()
            
            if nu_dato > kupon_dato:
                forslag_liste = forslag_str.split("; ")
                kupon_vundet = True
                
                for f in forslag_liste:
                    match_hold = re.search(r'\[(.*?)\]', f)
                    if match_hold:
                        hold_par = match_hold.group(1).split("-")
                        if len(hold_par) == 2:
                            hj_hold = hold_par[0].strip()
                            ud_hold = hold_par[1].strip()
                            
                            live_stats = match_stats_api.hent_avancerede_match_stats(hj_hold, ud_hold, kupon_dato_str)
                            linje_vundet = evaluer_enkelt_forslag(f, live_stats)
                            if not linje_vundet:
                                kupon_vundet = False
                                break
                
                endelig_status = "Vundet" if kupon_vundet else "Tabt"
                cursor.execute("UPDATE kupon_historik SET status = ? WHERE id = ?", (endelig_status, kupon_id))
                database_opdateret = True
                
        if database_opdateret:
            conn.commit()
            conn.close()
            gem_data.push_database_til_github()
        else:
            conn.close()
            
    except Exception:
        pass

def vis_auto_resultat_og_rapport():
    """
    Backup-funktion så jeres oprindelige kald i Kupon_Historik.py ikke fejler
    """
    pass

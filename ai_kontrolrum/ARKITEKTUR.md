# Odds Robot Pro – Live Arkitektur & Systemregler

## Ufravigelige Regler
1. `app.py` er 100 % LÅST og må aldrig ændres.
2. Alle nye funktioner bygges isoleret i undermapper (`udvidelser/`, `odds_motor/`, `historik/`).
3. Maks. 3.000 tegn pr. kodeblok/opdatering (eller eksisterende filgrænse overholdes).
4. Ingen gætteri: Tjek altid eksisterende funktioner i dette arkitektur-kort før ændringer.

## Komplet Fil- & Funktionsoversigt
- `app.py` (2885t): `dansk_tid`
- `tidsstyring/dansk_tid.py` (1578t): `hent_dansk_nu`, `formater_dansk_tid`, `konverter_til_dansk`, `vaelg_tidsramme`
- `kampprogram/hent_kampe.py` (1139t): `hent_aegte_kampe_fra_nettet`
- `odds_motor/autopilot_scanner.py` (6744t): `_hent_kampe_v9`, `_vurder_kupon`, `_gem_auto_cb`, `vis_autopilot_scanner`
- `odds_motor/autopilot_hjaelp.py` (3466t): `_gæt_liga_kode`, `har_skud_marked`, `_hent_live_valg`, `rens_kamp_valg`, `udvaelg_kandidater`, `vurder_top3`
- `odds_motor/autopilot_kamp_feed.py` (3781t): `_parse_event`, `hent_kampe_v9`
- `odds_motor/manuel_scanner.py` (5519t): `vis_manuel_scanner`
- `odds_motor/manuel_hjaelp.py` (6162t): `_form_til_dansk`, `_hent_ekstra_ctx`, `_find_spil_hold`, `begrundelse`, `_hent_kun_rigtigt_marked`, `_sikr_kamp`, `byg_forslag`
- `odds_motor/billed_ocr.py` (5195t): `_hent_gemini_noegle`, `_flet_billeder_til_et`, `_laes_med_gemini`, `udtraek_kupon_fra_flere_billeder`, `udtraek_kupon_fra_billede`
- `odds_motor/billed_hjaelp.py` (7222t): `_rens_holdnavn`, `_hent_live_vejr`, `_hent_dommer_og_kort`, `_tjek_bookmaker_udbud`, `analyser_kupon_kamp`, `_byg_intelligente_alternativer`, `samlet_kupon_analyse`
- `odds_motor/billed_parser.py` (9567t): `_normaliser_tekst`, `_er_dublet`, `_godt_og_skidt`, `vis_billed_scanner`
- `odds_motor/byg_kupon.py` (4939t): `beregn_sandsynlighed_fra_odds`, `_form_delta`, `_udtraek_espn_odds`, `_har_skud_marked`, `byg_kombineret_kupon`
- `odds_motor/dommer_intelligens.py` (5740t): `_h`, `_ren`, `_find_navn`, `_espn_dommer`, `_sportsdb_dommer`, `_bing_rss_dommer`, `hent_dommer`, `dommer_effekt`
- `odds_motor/kamp_intelligens.py` (7687t): `_h`, `_gaet_slug`, `til_decimal_odds`, `hurtig_kontekst`, `_hent_vejr_direkte`, `_hent_summary_data`, `_udtraek_h2h`, `berig_valgte_kampe`
- `odds_motor/liga_favoritter.py` (5226t): `normaliser_liga_navn`, `_send_favorit_event`, `hent_favorit_ligaer`, `tilfoej_ny_favorit_liga`, `fjern_favorit_liga`
- `odds_motor/multi_balancering.py` (865t): `beregn_lag_holder_odds`, `gem_balanceret_kupon`
- `historik/gem_data.py` (6940t): `_dansk_tid`, `_gh_cfg`, `_gh_url`, `_lokal_laes`, `_lokal_skriv`, `_gh_laes_direkte`, `_gh_skriv_direkte`, `_gh_laes`, `_gh_skriv`, `_baggrunds_sync`, `_vis_groen_bekraeftelse`, `hent_alle_kuponer`, `gem_kupon_i_historik`, `slet_kupon`
- `historik/regnskab_visning.py` (9800t): `_norm`, `_formater_ben`, `_hent_slutresultater`, `_match_hold`, `_vurd_ben`, `_auto_tjek_afventende`, `_handling`, `_tegn_kuponer`, `vis_regnskab`
- `udvidelser/autopilot_bro.py` (1513t): `hent_autopilot_valg_fra_api`
- `udvidelser/historik_statistik.py` (3565t): `hent_dommer_profil`, `hent_h2h_profil`, `hent_hold_profil`
- `udvidelser/holdnavne_oversaetter.py` (2290t): `normaliser_hold`, `samme_hold`
- `udvidelser/marked_motor.py` (2104t): `hent_reelle_muligheder`, `tjek_kupon_spil_mod_marked`
- `udvidelser/mobil_app.py` (3301t): `_indsaet_pwa_meta`, `vis_modul`
- `udvidelser/special_api.py` (3141t): `oversaet_da`, `hent_startopstilling`, `_gem_laert`, `hent_kamp_tilbud`, `_laes_fallback`
- `udvidelser/special_markeder.py` (3034t): `udtraek_alle_tilbud`, `vis_special_panel`
- `udvidelser/system_tjek.py`: `_scan_repo`, `vis_system_tjek`

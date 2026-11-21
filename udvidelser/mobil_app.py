import streamlit as st
import streamlit.components.v1 as components

FANE_TITEL = "📱 5. Mobil App & Reboot"


def _indsaet_pwa_meta():
    components.html(
        """
        <script>
        (function() {
            const doc = window.parent.document;
            const head = doc.head;
            if (!head.querySelector('meta[name="apple-mobile-web-app-capable"]')) {
                const m1 = doc.createElement('meta');
                m1.name = 'apple-mobile-web-app-capable';
                m1.content = 'yes';
                head.appendChild(m1);

                const m2 = doc.createElement('meta');
                m2.name = 'apple-mobile-web-app-status-bar-style';
                m2.content = 'black-translucent';
                head.appendChild(m2);

                const m3 = doc.createElement('meta');
                m3.name = 'apple-mobile-web-app-title';
                m3.content = 'Odds Robot Pro';
                head.appendChild(m3);

                const svgIcon = "data:image/svg+xml," + encodeURIComponent(
                    '<svg xmlns="http://w3.org" viewBox="0 0 180 180">' +
                    '<rect width="180" height="180" rx="40" fill="#0f172a"/>' +
                    '<text x="90" y="118" font-size="96" text-anchor="middle">🤖</text>' +
                    '</svg>'
                );
                const link = doc.createElement('link');
                link.rel = 'apple-touch-icon';
                link.href = svgIcon;
                head.appendChild(link);
            }
        })();
        </script>
        """,
        height=0,
        width=0,
    )


def vis_modul():
    _indsaet_pwa_meta()

    st.subheader("📱 Mobil App & Hurtig Reboot")
    st.caption("Brug Odds Robot Pro som en rigtig iPhone-app i fuld skærm – alle opdateringer i GitHub slår automatisk igennem.")

    st.markdown("### 🔄 1. Genstart / Reboot Appen")
    st.write("Hvis cachen skal nulstilles efter en opdatering i GitHub:")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("⚡ Ryd RAM-cache nu", type="primary", use_container_width=True, key="btn_clear_ram"):
            st.cache_data.clear()
            for k in list(st.session_state.keys()):
                if k not in ("kupon_ram_cache", "kupon_sha"):
                    st.session_state.pop(k, None)
            st.success("✅ RAM-cache er nulstillet! Alle kampdata hentes friskt.")
            st.rerun()

    with c2:
        cloud_host = ".".join(["share", "streamlit", "io"])
        reboot_url = f"https://{cloud_host}/"
        st.link_button("🌐 Åbn Streamlit Cloud (Reboot)", reboot_url, use_container_width=True)

    st.caption("Tip: Du kan også trykke på **Manage app** nederst til højre på skærmen -> **⋮** -> **Reboot app**.")

    st.markdown("---")
    st.markdown("### 📲 2. Installer som Mobil App på iPhone (10 sek.)")
    st.info(
        "**Sådan får du Odds Robot Pro som app-ikon på din hjemmeskærm:**\n\n"
        "1. Tryk på **Del-ikonet** (firkanten med pil op ⬆️) nederst i Safari.\n"
        "2. Rul ned og tryk på **Føj til hjemmeskærm** (`Add to Home Screen`).\n"
        "3. Tryk på **Tilføj** øverst til højre.\n\n"
        "✅ **Auto-opdatering:** Hver gang vi retter eller bygger nyt i GitHub, opdaterer appen sig selv automatisk næste gang du åbner den!"
    )

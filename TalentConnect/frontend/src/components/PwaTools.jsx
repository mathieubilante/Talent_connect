import { useEffect, useState } from "react";

const isStandalone = () =>
  window.matchMedia?.("(display-mode: standalone)").matches || window.navigator.standalone === true;

/* Bouton « Installer l'application » : Chrome/Edge/Android proposent l'installation par un événement ;
   sur iPhone, il faut passer par le menu Partager (on affiche l'aide). */
export function InstallButton() {
  const [evt, setEvt] = useState(null);
  const [installed, setInstalled] = useState(isStandalone());
  const [help, setHelp] = useState(false);
  const isIos = /iphone|ipad|ipod/i.test(navigator.userAgent);

  useEffect(() => {
    const onPrompt = (e) => { e.preventDefault(); setEvt(e); };
    const onInstalled = () => { setInstalled(true); setEvt(null); };
    window.addEventListener("beforeinstallprompt", onPrompt);
    window.addEventListener("appinstalled", onInstalled);
    return () => { window.removeEventListener("beforeinstallprompt", onPrompt); window.removeEventListener("appinstalled", onInstalled); };
  }, []);

  if (installed) return null;
  if (evt) {
    return <button className="btn-outline install-btn" onClick={async () => { evt.prompt(); await evt.userChoice; setEvt(null); }}>📲 Installer l'application</button>;
  }
  if (isIos) {
    return (
      <>
        <button className="btn-outline install-btn" onClick={() => setHelp(true)}>📲 Installer</button>
        {help && (
          <div className="modal-back" onClick={() => setHelp(false)}>
            <div className="modal" style={{ maxWidth: 380 }} onClick={(e) => e.stopPropagation()}>
              <h3>Installer sur iPhone</h3>
              <p>1. Touchez le bouton <b>Partager</b> (carré avec une flèche) dans Safari.<br />2. Choisissez <b>« Sur l'écran d'accueil »</b>.</p>
              <button className="btn full" onClick={() => setHelp(false)}>Compris</button>
            </div>
          </div>
        )}
      </>
    );
  }
  return null;
}

export function OfflineBanner() {
  const [online, setOnline] = useState(navigator.onLine);
  useEffect(() => {
    const up = () => setOnline(true), down = () => setOnline(false);
    window.addEventListener("online", up);
    window.addEventListener("offline", down);
    return () => { window.removeEventListener("online", up); window.removeEventListener("offline", down); };
  }, []);
  if (online) return null;
  return <div className="api-warning">📡 Vous êtes hors ligne. Les données ne peuvent pas être chargées tant que la connexion n'est pas rétablie.</div>;
}

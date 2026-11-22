import { LANGS, getLang, setLang } from "../i18n.js";

export default function LangSwitch() {
  return (
    <select className="lang-switch" aria-label="Langue" value={getLang()}
            onChange={(e) => { setLang(e.target.value); window.location.reload(); }}>
      {LANGS.map(([code, label]) => <option key={code} value={code}>{label}</option>)}
    </select>
  );
}

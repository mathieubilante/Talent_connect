/* Illustrations animées (SVG + CSS) : aucune image externe n'est nécessaire. */

export function MatchArt() {
  return (
    <svg viewBox="0 0 320 220" className="art" role="img" aria-label="Score de compatibilité">
      <rect x="8" y="8" width="304" height="204" rx="20" className="art-card" />
      <circle cx="96" cy="108" r="52" className="gauge-bg" />
      <circle cx="96" cy="108" r="52" className="gauge-fill" transform="rotate(-90 96 108)" />
      <text x="96" y="116" textAnchor="middle" className="gauge-text">87%</text>
      <text x="96" y="186" textAnchor="middle" className="art-small">compatibilité</text>
      <g className="pop p1"><rect x="176" y="44" width="116" height="28" rx="14" className="chip-ok" /><text x="234" y="63" textAnchor="middle" className="chip-t">✓ python</text></g>
      <g className="pop p2"><rect x="176" y="82" width="116" height="28" rx="14" className="chip-ok" /><text x="234" y="101" textAnchor="middle" className="chip-t">✓ sql</text></g>
      <g className="pop p3"><rect x="176" y="120" width="116" height="28" rx="14" className="chip-ok" /><text x="234" y="139" textAnchor="middle" className="chip-t">✓ fastapi</text></g>
      <g className="pop p4"><rect x="176" y="158" width="116" height="28" rx="14" className="chip-miss" /><text x="234" y="177" textAnchor="middle" className="chip-t2">docker</text></g>
    </svg>
  );
}

export function CvArt() {
  return (
    <svg viewBox="0 0 320 220" className="art" role="img" aria-label="Analyse du CV">
      <rect x="8" y="8" width="304" height="204" rx="20" className="art-card" />
      <rect x="44" y="30" width="130" height="160" rx="10" className="doc" />
      <rect x="58" y="46" width="60" height="9" rx="4" className="line strong" />
      {[68, 84, 100, 116, 132, 148, 164].map((y, i) => (
        <rect key={y} x="58" y={y} width={i % 3 === 2 ? 70 : 100} height="6" rx="3" className="line" />
      ))}
      <rect x="40" y="30" width="138" height="10" className="scanbar" />
      <g className="pop p1"><rect x="196" y="52" width="92" height="28" rx="14" className="chip-ok" /><text x="242" y="71" textAnchor="middle" className="chip-t">python</text></g>
      <g className="pop p2"><rect x="196" y="92" width="92" height="28" rx="14" className="chip-ok" /><text x="242" y="111" textAnchor="middle" className="chip-t">sql</text></g>
      <g className="pop p3"><rect x="196" y="132" width="92" height="28" rx="14" className="chip-ok" /><text x="242" y="151" textAnchor="middle" className="chip-t">docker</text></g>
      <text x="242" y="186" textAnchor="middle" className="art-small">compétences détectées</text>
    </svg>
  );
}

export function ChatArt() {
  return (
    <svg viewBox="0 0 320 220" className="art" role="img" aria-label="TConnect IA">
      <rect x="8" y="8" width="304" height="204" rx="20" className="art-card" />
      <g className="pop p1"><rect x="110" y="26" width="190" height="40" rx="14" className="bubble-me" /><text x="205" y="51" textAnchor="middle" className="chip-t">Une lettre pour cette offre ?</text></g>
      <g className="pop p2"><rect x="24" y="80" width="214" height="56" rx="14" className="bubble-bot" />
        <text x="36" y="102" className="art-text">Voici votre lettre de motivation,</text>
        <text x="36" y="122" className="art-text">adaptée à l'offre. Modifiez-la !</text></g>
      <g className="pop p3"><rect x="24" y="150" width="86" height="40" rx="14" className="bubble-bot" />
        <circle cx="48" cy="170" r="5" className="typing d1" /><circle cx="67" cy="170" r="5" className="typing d2" /><circle cx="86" cy="170" r="5" className="typing d3" /></g>
      <circle cx="286" cy="176" r="18" className="bot-badge" /><text x="286" y="183" textAnchor="middle" fontSize="20">🤖</text>
    </svg>
  );
}

export function BellArt() {
  return (
    <svg viewBox="0 0 320 220" className="art" role="img" aria-label="Notifications">
      <rect x="8" y="8" width="304" height="204" rx="20" className="art-card" />
      <g className="bell-swing"><path d="M96 126c0-26 12-44 28-48v-6a8 8 0 0 1 16 0v6c16 4 28 22 28 48l10 14H86z" className="bell" /><circle cx="132" cy="150" r="9" className="bell" /></g>
      <circle cx="160" cy="66" r="12" className="badge-pulse" /><text x="160" y="71" textAnchor="middle" className="chip-t">3</text>
      <g className="pop p1"><rect x="190" y="52" width="108" height="34" rx="10" className="notif-card" /><text x="244" y="73" textAnchor="middle" className="art-text">✓ Candidature reçue</text></g>
      <g className="pop p2"><rect x="190" y="98" width="108" height="34" rx="10" className="notif-card" /><text x="244" y="119" textAnchor="middle" className="art-text">⭐ Présélectionné</text></g>
      <g className="pop p3"><rect x="190" y="144" width="108" height="34" rx="10" className="notif-card" /><text x="244" y="165" textAnchor="middle" className="art-text">📅 Entretien demain</text></g>
    </svg>
  );
}

export function LockArt() {
  return (
    <svg viewBox="0 0 320 220" className="art" role="img" aria-label="Documents protégés">
      <rect x="8" y="8" width="304" height="204" rx="20" className="art-card" />
      <circle cx="160" cy="112" r="64" className="ring r1" />
      <circle cx="160" cy="112" r="64" className="ring r2" />
      <rect x="128" y="104" width="64" height="52" rx="10" className="lock-body" />
      <path d="M140 104v-14a20 20 0 0 1 40 0v14" className="lock-shackle" />
      <circle cx="160" cy="128" r="6" className="lock-hole" /><rect x="157" y="130" width="6" height="14" rx="3" className="lock-hole" />
      <g className="pop p1"><rect x="30" y="40" width="84" height="26" rx="8" className="notif-card" /><text x="72" y="58" textAnchor="middle" className="art-text">🪪 CIN</text></g>
      <g className="pop p2"><rect x="206" y="40" width="90" height="26" rx="8" className="notif-card" /><text x="251" y="58" textAnchor="middle" className="art-text">📄 Patente</text></g>
      <g className="pop p3"><rect x="206" y="160" width="96" height="26" rx="8" className="notif-card" /><text x="254" y="178" textAnchor="middle" className="art-text">🔒 chiffré</text></g>
    </svg>
  );
}

export function HeroArt() {
  return (
    <div className="hero-floats" aria-hidden="true">
      <div className="float-card f1">💼 Stage Python · <b>92 %</b></div>
      <div className="float-card f2">✅ Candidature envoyée</div>
      <div className="float-card f3">🔔 Entretien demain 10 h</div>
      <div className="float-card f4">🤖 TConnect IA</div>
    </div>
  );
}

/* Service worker de TalentConnect : met en cache la coquille du site pour qu'il s'ouvre
   comme une application, même avec une connexion instable. Les appels à l'API ne sont JAMAIS mis en cache. */
const VERSION = "tc-v1";
const STATIC = `${VERSION}-static`;
const SHELL = ["/", "/offline.html", "/manifest.webmanifest", "/favicon.svg", "/icons/icon-192.png", "/icons/icon-512.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(STATIC).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => !k.startsWith(VERSION)).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;            // l'API est sur un autre domaine : on n'y touche pas

  if (req.mode === "navigate") {                              // pages : réseau d'abord, sinon dernière version connue
    e.respondWith(
      fetch(req)
        .then((res) => { const copy = res.clone(); caches.open(STATIC).then((c) => c.put("/", copy)); return res; })
        .catch(() => caches.match("/").then((r) => r || caches.match("/offline.html")))
    );
    return;
  }
  if (url.pathname.startsWith("/assets/") || url.pathname.startsWith("/icons/") || url.pathname === "/favicon.svg") {
    e.respondWith(                                            // fichiers du site : cache d'abord
      caches.match(req).then((hit) => hit || fetch(req).then((res) => {
        const copy = res.clone();
        caches.open(STATIC).then((c) => c.put(req, copy));
        return res;
      }))
    );
  }
});

const targets = [
  "http://localhost:3011/",
  "http://localhost:3011/login",
  "http://localhost:3011/documents",
  "http://localhost:3011/api/v1/health",
  "http://localhost:8060/health",
];

for (const url of targets) {
  const start = Date.now();
  try {
    const response = await fetch(url, {
      signal: AbortSignal.timeout(10000),
      cache: "no-store",
    });
    const text = await response.text();
    console.log("URL", url);
    console.log("STATUS", response.status);
    console.log("MS", Date.now() - start);
    console.log("HEADERS", JSON.stringify(Object.fromEntries(response.headers.entries())));
    console.log("BODY", text.slice(0, 400).replace(/\n/g, " "));
    console.log("---");
  } catch (error) {
    const code = error?.cause?.code || error?.code || error?.name;
    console.log("URL", url);
    console.log("ERROR", code, error?.message || String(error));
    console.log("MS", Date.now() - start);
    console.log("---");
  }
}

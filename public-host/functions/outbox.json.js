export async function onRequestGet(context) {
  const worker = await import("../worker.js");
  const url = new URL(context.request.url);
  url.pathname = "/outbox.json";
  return worker.default.fetch(new Request(url.toString(), context.request), context.env);
}

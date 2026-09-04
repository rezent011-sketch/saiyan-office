export async function onRequestGet(context) {
  const worker = await import("../worker.js");
  return worker.default.fetch(context.request, context.env);
}

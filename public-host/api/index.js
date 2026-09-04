export const config = { runtime: "edge" };

import worker from "../worker.js";

export default function handler(request) {
  return worker.fetch(request);
}

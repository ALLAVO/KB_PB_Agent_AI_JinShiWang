// src/api/intention.js
export async function fetchIntention(text) {
  const response = await fetch("http://localhost:8000/api/v1/intention", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text })
  });
  return response.json();
}

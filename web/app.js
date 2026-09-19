async function getJson(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

function render(object) {
  const pre = document.createElement("pre");
  pre.textContent = JSON.stringify(object, null, 2);
  return pre;
}

async function refresh() {
  try {
    document.querySelector("#health").replaceChildren(render(await getJson("/health")));
    document.querySelector("#providers").replaceChildren(render(await getJson("/providers")));
    document.querySelector("#latest").replaceChildren(render(await getJson("/runs/latest")));
  } catch (error) {
    document.querySelector("#latest").textContent = "No run recorded yet.";
  }
}

document.querySelector("#refresh").addEventListener("click", refresh);
refresh();

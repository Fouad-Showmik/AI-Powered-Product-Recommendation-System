"use strict";

const API = window.APP_CONFIG.API_BASE.replace(/\/$/, "");
const app = document.getElementById("app");
const form = document.getElementById("search-form");
const input = document.getElementById("search-input");

const money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

/* ------------------------------------------------------------------ helpers */

// Build DOM nodes without innerHTML, so text from the API can never run as HTML.
function el(tag, props = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (key === "class") node.className = value;
    else if (key === "text") node.textContent = value;
    else node.setAttribute(key, value);
  }
  for (const child of children.flat()) if (child != null) node.append(child);
  return node;
}

async function api(path, options) {
  let res;
  try {
    res = await fetch(API + path, options);
  } catch {
    throw new Error("Cannot reach the server. Check that the API is running.");
  }
  if (res.status === 404) throw new Error("NOT_FOUND");
  if (res.status === 502) throw new Error("The search service is temporarily unavailable. Please try again.");
  if (!res.ok) throw new Error("Something went wrong (error " + res.status + ").");
  return res.json();
}

function show(...nodes) {
  app.replaceChildren(...nodes);
}

function stateBox(title, message, isError = false) {
  return el("div", { class: "state" + (isError ? " error" : "") }, el("strong", { text: title }), message);
}

function loadingGrid(count = 8) {
  return el("div", { class: "grid" }, Array.from({ length: count }, () => el("div", { class: "skeleton" })));
}

function productImage(product) {
  if (!product.image_url) return el("div", { class: "img-fallback", text: "No image" });
  const img = el("img", { src: product.image_url, alt: product.name, loading: "lazy" });
  img.addEventListener("error", () => img.replaceWith(el("div", { class: "img-fallback", text: "No image" })));
  return img;
}

function productCard(product) {
  return el(
    "a",
    { class: "card", href: "#/product/" + encodeURIComponent(product.id) },
    productImage(product),
    el(
      "div",
      { class: "card-body" },
      product.category ? el("span", { class: "category", text: product.category }) : null,
      el("span", { class: "name", text: product.name }),
      el(
        "div",
        { class: "meta" },
        el("span", { text: "★ " + product.rating.toFixed(1) }),
        product.price != null ? el("span", { class: "price", text: money.format(product.price) }) : null
      )
    )
  );
}

function productGrid(products) {
  return el("div", { class: "grid" }, products.map(productCard));
}

/* -------------------------------------------------------------------- views */

let renderId = 0; // ignores slow responses from pages the user already left

async function viewHome() {
  const id = ++renderId;
  input.value = "";
  document.title = "Product Finder";
  show(el("h1", { text: "All products" }), el("p", { class: "subtle", text: "Search above, or click a product to see similar ones." }), loadingGrid());
  try {
    const products = await api("/products?limit=100");
    if (id !== renderId) return;
    show(
      el("h1", { text: "All products" }),
      el("p", { class: "subtle", text: products.length + " products. Search above, or click one to see similar items." }),
      productGrid(products)
    );
  } catch (err) {
    if (id === renderId) show(stateBox("Couldn’t load products", err.message, true));
  }
}

async function viewSearch(query) {
  const id = ++renderId;
  input.value = query;
  document.title = query + " – Product Finder";
  show(el("h1", { text: "Results for “" + query + "”" }), el("p", { class: "subtle", text: "Searching…" }), loadingGrid(4));
  try {
    const data = await api("/recommendations/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
    if (id !== renderId) return;
    const products = data.results.map((r) => r.product);
    if (products.length === 0) {
      show(
        el("h1", { text: "Results for “" + query + "”" }),
        stateBox("No close matches", "Try different words, or describe what you want to use it for."),
        el("a", { class: "back", href: "#/", text: "← Browse all products" })
      );
      return;
    }
    show(
      el("h1", { text: "Results for “" + query + "”" }),
      el("p", { class: "subtle", text: products.length + (products.length === 1 ? " product" : " products") + ", best match first" }),
      productGrid(products)
    );
  } catch (err) {
    if (id === renderId) show(stateBox("Search failed", err.message, true));
  }
}

async function viewProduct(productId) {
  const id = ++renderId;
  show(el("a", { class: "back", href: "#/", text: "← All products" }), el("div", { class: "skeleton" }));

  let product;
  try {
    product = await api("/products/" + encodeURIComponent(productId));
  } catch (err) {
    if (id !== renderId) return;
    show(
      el("a", { class: "back", href: "#/", text: "← All products" }),
      err.message === "NOT_FOUND" ? stateBox("Product not found", "It may have been removed.") : stateBox("Couldn’t load product", err.message, true)
    );
    return;
  }
  if (id !== renderId) return;

  document.title = product.name + " – Product Finder";
  const similarBox = el("div", {}, loadingGrid(4));

  show(
    el("a", { class: "back", href: "javascript:history.back()", text: "← Back" }),
    el(
      "section",
      { class: "detail" },
      productImage(product),
      el(
        "div",
        {},
        product.category ? el("span", { class: "category", text: product.category }) : null,
        el("h1", { text: product.name }),
        el("div", { class: "meta" }, el("span", { text: "★ " + product.rating.toFixed(1) + " / 5" })),
        product.price != null ? el("span", { class: "price", text: money.format(product.price) }) : null,
        el("p", { text: product.description })
      )
    ),
    el("h2", { text: "Similar products" }),
    similarBox
  );
  window.scrollTo(0, 0);

  // The tapped product itself is already excluded by the API.
  try {
    const data = await api("/products/" + encodeURIComponent(productId) + "/similar");
    if (id !== renderId) return;
    const products = data.results.map((r) => r.product);
    similarBox.replaceChildren(
      products.length ? productGrid(products) : stateBox("No similar products yet", "Nothing in the catalogue is close enough to this one.")
    );
  } catch (err) {
    if (id === renderId) similarBox.replaceChildren(stateBox("Couldn’t load similar products", err.message, true));
  }
}

/* ------------------------------------------------------------------- router */

function route() {
  const hash = location.hash || "#/";
  let match;

  if ((match = hash.match(/^#\/product\/(.+)$/))) {
    viewProduct(safeDecode(match[1]));
  } else if ((match = hash.match(/^#\/search\/(.+)$/))) {
    viewSearch(safeDecode(match[1]));
  } else {
    viewHome();
  }
  if (!hash.startsWith("#/product/")) window.scrollTo(0, 0);
}

function safeDecode(value) {
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

// One search = one embedding API call on the backend, so search on submit, not on every keystroke.
form.addEventListener("submit", (event) => {
  event.preventDefault();
  const query = input.value.trim();
  if (!query) return;
  const target = "#/search/" + encodeURIComponent(query);
  if (location.hash === target) route();
  else location.hash = target;
});

window.addEventListener("hashchange", route);
route();
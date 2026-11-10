/* MediaTracker shell behaviour: bottom sheets, toasts, form busy states, offline banner.
   Plain JS, no build step. HTMX handles the requests. */
(() => {
  "use strict";

  const reduceMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const buzz = (ms) => { if (navigator.vibrate) navigator.vibrate(ms); };

  /* Toasts */
  const toastRegion = () => document.getElementById("toasts");

  function showToast(el) {
    const duration = Number(el.dataset.duration) || 3200;
    setTimeout(() => {
      el.classList.add("toast--out");
      setTimeout(() => el.remove(), reduceMotion() ? 0 : 240);
    }, duration);
  }

  function toast(text, { error = false, undo = null, region = toastRegion() } = {}) {
    if (!region) return;
    // One undo on offer at a time: rapid +1s should not stack a tower of toasts.
    region.querySelectorAll("[data-has-undo]").forEach((old) => old.remove());
    const el = document.createElement("div");
    el.className = "toast" + (error ? " toast--error" : "");
    el.dataset.duration = error ? "6000" : undo ? "5000" : "3200";
    el.textContent = text;
    if (undo) {
      el.dataset.hasUndo = "1";
      el.classList.add("toast--action");
      const action = document.createElement("button");
      action.type = "button";
      action.className = "toast__action";
      action.textContent = "Undo";
      action.addEventListener("click", () => { el.remove(); undo(); });
      el.append(action);
    }
    region.append(el);
    showToast(el);
    return el;
  }
  window.MT = Object.assign(window.MT || {}, { toast });

  document.querySelectorAll("[data-toast]").forEach(showToast);
  // The server can ask for a toast with an HX-Trigger header: {"toast": "Saved"}.
  document.body.addEventListener("toast", (e) => {
    const detail = typeof e.detail === "string" ? { value: e.detail } : e.detail;
    if (!detail?.undo) { toast(detail?.value); return; }
    const body = new URLSearchParams();
    if (detail.n) body.set("n", detail.n);
    toast(detail.value, { undo: () => enqueue({ url: detail.undo, body: body.toString(), label: "Undo" }) });
  });

  /* What a log earned, beside the log's own toast. Quick +1s replace it, not stack it. A +1 usually
     opens the rate sheet in the same breath, and a modal covers the page's toasts, so with a sheet
     open this one goes in a popover, the only thing that can sit above a modal. */
  document.body.addEventListener("chud-earned", (e) => {
    document.querySelectorAll("[data-chud]").forEach((old) => old.remove());
    const over = document.querySelector("dialog[open]") ? document.getElementById("toasts-over") : null;
    const el = toast(e.detail.value, over ? { region: over } : {});
    if (el) el.dataset.chud = "1";
    if (over?.showPopover) {
      if (over.matches(":popover-open")) over.hidePopover();
      over.showPopover();
    }
  });

  /* Bottom sheets: server sends a <dialog data-sheet>, we open it as a modal.
     The browser provides the focus trap, inert background and Escape. */
  function openSheet(dialog) {
    // Only itself: another sheet may already have taken the host by the time this has slid away.
    dialog.addEventListener("close", () => {
      setTimeout(() => dialog.remove(), reduceMotion() ? 0 : 320);
    });
    dialog.addEventListener("click", (e) => { if (e.target === dialog) dialog.close(); });
    dialog.addEventListener("cancel", () => buzz(5));
    dialog.querySelectorAll("[data-sheet-close]").forEach((b) => b.addEventListener("click", () => dialog.close()));
    dialog.showModal();
    // Land on the title, not the first input, so a phone keyboard does not pop up over the sheet.
    dialog.querySelector("[autofocus]")?.focus({ preventScroll: true });
    makeDraggable(dialog);
  }

  const openPendingSheet = () => {
    const dialog = document.querySelector("#sheet-host dialog[data-sheet]:not([open])");
    if (dialog) openSheet(dialog);
  };
  document.body.addEventListener("htmx:afterSwap", openPendingSheet);
  const closeSheet = () => document.querySelector("#sheet-host dialog[open]")?.close();
  document.body.addEventListener("sheet-close", closeSheet);

  /* A level-up waits its turn behind whatever sheet is open, as in the prototype. Still unanswered
     on the next page, the shell asks again. */
  let levelUpTimer = null;
  function offerLevelUp(url) {
    clearTimeout(levelUpTimer);
    if (!navigator.onLine) return;
    if (document.querySelector("#sheet-host dialog")) {
      levelUpTimer = setTimeout(() => offerLevelUp(url), 500);
      return;
    }
    buzz(20);
    window.htmx?.ajax("GET", url, { target: "#sheet-host", swap: "innerHTML" })?.catch(() => {});
  }
  document.body.addEventListener("chud-level-up", (e) => offerLevelUp(e.detail.url));
  const waitingLevelUp = document.querySelector("[data-level-up]");
  if (waitingLevelUp) offerLevelUp(waitingLevelUp.dataset.levelUp);

  /* A poller keeps trying on its own and only says something once it has missed a few. A
     typeahead failure goes where the results would have been. Everything else is a toast. */
  function requestFailed(e, detail) {
    const element = e.detail.elt;
    const poller = element?.closest?.("[data-poll]");
    if (poller) {
      const misses = Number(poller.dataset.misses || 0) + 1;
      poller.dataset.misses = misses;
      if (misses >= 3) poller.querySelector("[data-poll-error]")?.removeAttribute("hidden");
      return;
    }
    if (e.detail.target?.id === "search-panel") {
      showSearchError(element, detail);
      return;
    }
    toast(`Couldn't load that (${detail}). Try again.`, { error: true });
  }
  document.body.addEventListener("htmx:responseError", (e) => requestFailed(e, `HTTP ${e.detail.xhr.status}`));
  document.body.addEventListener("htmx:sendError", (e) => requestFailed(e, "no answer from the server"));

  function showSearchError(input, detail) {
    const box = document.createElement("div");
    box.className = "inline-error";
    box.setAttribute("role", "alert");
    box.style.margin = "4px 16px";
    const line = document.createElement("p");
    const head = document.createElement("strong");
    head.textContent = "Couldn't search.";
    const small = document.createElement("small");
    small.textContent = detail;
    line.append(head, " ", small);
    const retry = document.createElement("button");
    retry.type = "button";
    retry.className = "btn btn--small btn--outline";
    retry.textContent = "Try again";
    retry.addEventListener("click", () => window.htmx?.trigger(input, "search"));
    box.append(line, retry);
    document.getElementById("search-panel").replaceChildren(box);
  }

  /* Coming back to a page with text in the search box puts the results back. */
  const searchBox = document.querySelector('.search input[type="search"]');
  const searchPanel = document.getElementById("search-panel");
  window.addEventListener("pageshow", () => {
    if (searchBox?.value && searchPanel && !searchPanel.childElementCount) {
      window.htmx?.trigger(searchBox, "search");
    }
  });

  /* Posters. The server answers with a 1px stand-in while the worker fetches the real file,
     so a load with no real size means try again shortly. */
  const POSTER_RETRIES = [2500, 6000, 15000];
  function posterSettled(img) {
    if (img.naturalWidth > 1) {
      img.classList.add("is-loaded");
      return;
    }
    const tries = Number(img.dataset.tries || 0);
    if (tries >= POSTER_RETRIES.length) return;
    img.dataset.tries = tries + 1;
    setTimeout(() => {
      if (!img.isConnected) return;
      const url = new URL(img.src);
      url.searchParams.set("try", tries + 1);
      img.src = url.href;
    }, POSTER_RETRIES[tries]);
  }
  document.addEventListener("load", (e) => { if (e.target.matches?.("img[data-poster]")) posterSettled(e.target); }, true);
  document.querySelectorAll("img[data-poster]").forEach((img) => { if (img.complete) posterSettled(img); });

  /* Back: where you came from when that was this app, otherwise the link's own target. */
  document.addEventListener("click", (e) => {
    const back = e.target.closest?.("[data-back]");
    if (!back) return;
    const here = window.location.origin;
    if (document.referrer.startsWith(here) && window.history.length > 1) {
      e.preventDefault();
      window.history.back();
    }
  });

  /* Swipe down to close. Drag from the handle, or from the panel when it is scrolled to the top. */
  function makeDraggable(dialog) {
    const panel = dialog.querySelector(".sheet__panel");
    let startY = 0, startT = 0, dy = 0, active = false;

    const begin = (e) => {
      if (e.isPrimary === false) return;
      const fromHandle = e.target.closest("[data-sheet-grab]");
      if (!fromHandle && panel.scrollTop > 0) return;
      // A drag that starts on a control would capture the pointer and swallow its click.
      if (e.target.closest("button, a, input, label, select, textarea, [data-stars]")) return;
      active = true; startY = e.clientY; startT = e.timeStamp; dy = 0;
      try { dialog.setPointerCapture(e.pointerId); } catch { /* synthetic or already released pointer */ }
      dialog.classList.add("sheet--dragging");
    };
    const move = (e) => {
      if (!active) return;
      const raw = e.clientY - startY;
      // Friction when pulling up, free movement when pulling down.
      dy = raw < 0 ? raw / 6 : raw;
      dialog.style.transform = `translateY(${dy}px)`;
    };
    const end = (e) => {
      if (!active) return;
      active = false;
      dialog.classList.remove("sheet--dragging");
      const velocity = dy / Math.max(1, e.timeStamp - startT);
      dialog.style.transform = "";
      if (dy > 120 || velocity > 0.5) { buzz(8); dialog.close(); }
    };
    dialog.addEventListener("pointerdown", begin);
    dialog.addEventListener("pointermove", move);
    dialog.addEventListener("pointerup", end);
    dialog.addEventListener("pointercancel", end);
  }

  /* Forms: busy state on submit, no double submit, confirm on destructive actions. */
  document.addEventListener("submit", (e) => {
    const form = e.target;
    const message = form.dataset.confirm;
    if (message && !window.confirm(message)) { e.preventDefault(); return; }
    if (form.dataset.submitting === "1") { e.preventDefault(); return; }
    if (form.matches("[data-validate]") && !form.checkValidity()) return;
    if (form.hasAttribute("data-busy-form")) {
      form.dataset.submitting = "1";
      const button = form.querySelector("[data-busy-button]");
      if (button) {
        button.setAttribute("aria-busy", "true");
        button.dataset.label = button.textContent;
        button.textContent = form.dataset.busyText || "Working";
        // Disable on the next tick so the button's own value is still submitted.
        setTimeout(() => { button.disabled = true; }, 0);
      }
    }
  });
  // Coming back via the back button must not leave a form stuck in its busy state.
  window.addEventListener("pageshow", (e) => {
    if (!e.persisted) return;
    document.querySelectorAll("form[data-submitting]").forEach((form) => {
      delete form.dataset.submitting;
      const button = form.querySelector("[data-busy-button]");
      if (button) { button.disabled = false; button.removeAttribute("aria-busy"); button.textContent = button.dataset.label || button.textContent; }
    });
  });

  /* Inline validation: show the browser's message under a field once it has been left. */
  const showFieldError = (input) => {
    const slot = input.form?.querySelector(`[data-error-for="${input.name}"]`);
    if (!slot) return;
    const form = input.form;
    if (input.name === "password_confirm" && form.elements.password) {
      input.setCustomValidity(input.value && input.value !== form.elements.password.value ? "The two passwords do not match." : "");
    }
    slot.textContent = input.validity.valid ? "" : input.validationMessage;
    input.closest(".field")?.classList.toggle("field--error", !input.validity.valid);
  };
  document.addEventListener("focusout", (e) => {
    if (e.target.matches?.("form[data-validate] input")) showFieldError(e.target);
  });
  document.addEventListener("input", (e) => {
    const input = e.target;
    if (input.matches?.("form[data-validate] input") && input.closest(".field--error")) showFieldError(input);
  });

  /* A form that came back with errors puts focus on the first bad field. */
  document.querySelector(".field--error input")?.focus({ preventScroll: false });

  /* Copy a code. */
  document.addEventListener("click", async (e) => {
    const button = e.target.closest("[data-copy]");
    if (!button) return;
    try {
      await navigator.clipboard.writeText(button.dataset.copy);
      button.classList.add("is-copied");
      toast("Code copied");
      buzz(8);
      setTimeout(() => button.classList.remove("is-copied"), 1600);
    } catch {
      toast("Couldn't copy. Select the code and copy it by hand.", { error: true });
    }
  });

  /* Writes. Everything that changes the diary goes through one queue kept in localStorage, so
     a +1 on a train is not lost: it is shown straight away, sent in order, retried quietly, and
     waits for the connection if it has to. Replaying one is safe, because each names what it
     meant ("episode 5"), not "one more". The server answers with out-of-band fragments.
     One queue per member: on a shared phone, one member's writes must never go out as another's.
     Signed out there is nobody to send as, so nothing runs. */
  const MEMBER = document.body.dataset.user;
  const QUEUE = `mt.writes.${MEMBER}`;
  const FAILED = "mt.failed";
  const RETRIES = [400, 1200];
  const WAIT_ONLINE = 15000;
  const held = [];
  let draining = false;
  let again = false;
  let waitTimer = null;

  const readQueue = () => {
    try { return JSON.parse(localStorage.getItem(QUEUE)) || []; } catch { return []; }
  };
  const writeQueue = (items) => { localStorage.setItem(QUEUE, JSON.stringify(items)); syncBanner(); };
  const removeFromQueue = (item) => writeQueue(readQueue().filter((queued) => queued.id !== item.id));
  const delay = (ms) => new Promise((done) => setTimeout(done, ms));
  const csrfToken = () => {
    try { return JSON.parse(document.body.getAttribute("hx-headers"))["X-CSRFToken"]; } catch { return ""; }
  };

  const offline = document.getElementById("offline");
  function syncBanner() {
    if (!offline) return;
    const waiting = readQueue().length;
    offline.hidden = navigator.onLine && !waiting;
    const count = waiting ? `${waiting} ${waiting === 1 ? "log" : "logs"} waiting to sync.` : "";
    offline.textContent = navigator.onLine
      ? count
      : `You're offline. ${count || "What you have already opened still works."}`;
  }

  /* Fragments for what is not on this page are dropped rather than left to htmx to complain
     about, which is what lets the server send everything a change touched. */
  function applyHtml(html) {
    const template = document.createElement("template");
    template.innerHTML = html;
    template.content.querySelectorAll("[hx-swap-oob]").forEach((el) => {
      if (!document.getElementById(el.id)) el.remove();
    });
    const rest = template.innerHTML.trim();
    if (rest && window.htmx) window.htmx.swap(document.body, rest, { swapStyle: "none" });
    openPendingSheet();
  }

  function applyTriggers(header) {
    if (!header) return;
    let events = {};
    try { events = JSON.parse(header); } catch { return; }
    Object.entries(events).forEach(([name, detail]) => {
      document.body.dispatchEvent(new CustomEvent(name, { detail }));
    });
  }

  function withoutSheet(html) {
    const template = document.createElement("template");
    template.innerHTML = html;
    template.content.querySelector("#sheet-host[hx-swap-oob]")?.remove();
    return template.innerHTML;
  }

  function flushHeld() {
    // Applied once the queue is empty: an answer to an earlier +1 would wind the count back.
    // Only the last sheet opens: three quick +1s ask about one episode, not three. Not always the
    // last answer: a double tap's second answer changed nothing and brings no sheet.
    const answers = held.splice(0);
    const lastSheet = answers.findLastIndex(({ html }) => html.includes('id="sheet-host"'));
    answers.forEach(({ html, triggers }, index) => {
      if (triggers && JSON.parse(triggers)["sheet-close"]) closeSheet();
      applyHtml(index === lastSheet ? html : withoutSheet(html));
      applyTriggers(triggers);
    });
    document.querySelectorAll("[data-pending]").forEach((el) => delete el.dataset.pending);
  }

  /* A failure the page can't explain on its own: put the page back to what the server holds,
     then say what went wrong where the action was, with a way to try again. */
  function failed(item, detail) {
    // Off the queue first, or the reload would send it again and fail again, forever.
    removeFromQueue(item);
    sessionStorage.setItem(FAILED, JSON.stringify({ ...item, detail }));
    window.location.reload();
  }

  async function send(item) {
    for (let attempt = 0; ; attempt += 1) {
      let response = null;
      try {
        response = await fetch(item.url, {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": csrfToken(),
            "HX-Request": "true",
            // Which page this answer lands on, as htmx sends on its own requests.
            "HX-Current-URL": window.location.href,
            // How many episode rows this page has loaded, so only those are sent back.
            "X-Episode-Rows": String(document.querySelectorAll("[data-episode]").length),
          },
          body: item.body,
        });
      } catch {
        response = null;
      }
      if (response?.redirected && new URL(response.url).pathname.startsWith("/login")) {
        // Signed out. The write stays queued and goes through after signing back in.
        window.location.href = `/login/?next=${encodeURIComponent(window.location.pathname)}`;
        return "stop";
      }
      if (response?.ok) {
        held.push({ html: await response.text(), triggers: response.headers.get("HX-Trigger") });
        return "sent";
      }
      if (response && response.status < 500) {
        const text = await response.text();
        if (item.wait && text.includes("data-sheet")) {
          document.getElementById("sheet-host").innerHTML = text;
          window.htmx?.process(document.getElementById("sheet-host"));
          openPendingSheet();
          return "gone";
        }
        failed(item, `HTTP ${response.status}${text && text.length < 200 ? `: ${text}` : ""}`);
        return "stop";
      }
      if (attempt < RETRIES.length) { await delay(RETRIES[attempt]); continue; }
      if (response) {
        failed(item, `HTTP ${response.status}`);
        return "stop";
      }
      if (item.wait) {
        closeSheet();
        toast("Saved on this device. It will sync when the connection is back.");
      }
      return "wait";
    }
  }

  async function sendAll() {
    while (navigator.onLine) {
      const [item] = readQueue();
      if (!item) break;
      const outcome = await send(item);
      if (outcome === "stop") return;
      if (outcome === "wait") { waitTimer = setTimeout(drain, WAIT_ONLINE); break; }
      removeFromQueue(item);
    }
    if (!readQueue().length) flushHeld();
  }

  /* Two tabs share the queue. Whichever holds the lock sends. The other looks again shortly, so
     its own spinners clear once the queue has emptied. */
  async function drain() {
    if (!MEMBER || draining) return;
    draining = true;
    clearTimeout(waitTimer);
    try {
      if (!navigator.locks) {
        await sendAll();
      } else {
        await navigator.locks.request(QUEUE, { ifAvailable: true }, async (lock) => {
          if (lock) await sendAll();
          else waitTimer = setTimeout(drain, 1000);
        });
      }
    } finally {
      draining = false;
    }
    if (again) { again = false; drain(); }
  }

  /* One key per deliberate send. randomUUID needs a secure context, which a phone reaching the
     app over plain http on the LAN is not, so there are two ways down. */
  function newKey() {
    if (window.crypto?.randomUUID) return window.crypto.randomUUID();
    if (window.crypto?.getRandomValues) {
      return Array.from(window.crypto.getRandomValues(new Uint8Array(16)), (b) => b.toString(16).padStart(2, "0")).join("");
    }
    return `${Date.now().toString(16)}${Math.random().toString(16).slice(2)}${Math.random().toString(16).slice(2)}`;
  }

  function enqueue(item) {
    writeQueue([...readQueue(), { ...item, id: `${Date.now()}-${Math.random()}` }]);
    if (draining) again = true;
    drain();
  }

  /* The day it was pressed, by the phone's clock: it is the phone's evening that counts, and a
     queued write may not arrive until tomorrow. */
  function localDate() {
    const now = new Date();
    const pad = (n) => String(n).padStart(2, "0");
    return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
  }

  /* A like shows at once: the heart fills and the count moves, then the answer settles it. */
  function likeOptimistically(form) {
    const button = form.querySelector("button");
    const input = form.elements.on;
    const liking = input.value === "1";
    const count = button.querySelector("[data-count]");
    const next = Math.max(0, Number(count.textContent) + (liking ? 1 : -1));
    count.textContent = next;
    button.classList.toggle("is-on", liking);
    button.setAttribute("aria-pressed", liking ? "true" : "false");
    button.setAttribute("aria-label", `Like, ${next}`);
    button.querySelector("svg")?.setAttribute("fill", liking ? "currentColor" : "none");
    input.value = liking ? "0" : "1";
    buzz(8);
  }

  function stepOptimistically(form) {
    const input = form.elements.n;
    const unit = Number(input.value);
    const done = Number(form.dataset.done) + 1;
    const total = Number(form.dataset.total) || null;
    const next = unit + 1;
    const word = form.dataset.word;
    const finished = total && !form.dataset.openEnded && done >= total;
    form.dataset.done = done;
    input.value = next;
    const info = document.getElementById(form.dataset.info);
    if (info) {
      const nextLine = info.querySelector("[data-next]");
      if (nextLine && !finished) nextLine.textContent = `Next: ${word} ${next}`;
      const progress = info.querySelector("[data-progress]");
      if (progress) progress.textContent = `${done} / ${total || "?"}`;
      const bar = info.querySelector("[data-bar]");
      if (bar && total) bar.style.width = `${Math.min(100, Math.round((done / total) * 100))}%`;
    }
    const button = form.querySelector("button");
    button.setAttribute("aria-label", `Log ${word.toLowerCase()} ${next} of ${form.dataset.title}`);
    button.dataset.pending = "1";
    if (finished) {
      button.disabled = true;
      document.getElementById(form.dataset.row)?.classList.add("is-leaving");
    }
    if (!reduceMotion()) {
      const float = document.createElement("span");
      float.className = "plus__float";
      float.textContent = "+1";
      float.addEventListener("animationend", () => float.remove());
      button.append(float);
    }
    buzz(8);
  }

  document.addEventListener("submit", (e) => {
    const form = e.target;
    if (!form.matches?.("form[data-write]") || e.defaultPrevented) return;
    e.preventDefault();
    const body = new URLSearchParams(new FormData(form));
    body.set("local_date", localDate());
    // A send that must happen once gets its own key now, when the member pressed it. A page
    // drawn offline has only the one the server gave it, which every send would share.
    if (form.hasAttribute("data-once")) body.set("token", newKey());
    const wait = form.dataset.write === "wait" && navigator.onLine;
    // A button can send the same fields somewhere else, as Skip does beside Post.
    const chosen = e.submitter;
    enqueue({
      url: chosen?.getAttribute("formaction") || form.getAttribute("action"),
      body: body.toString(),
      label: chosen?.dataset.label || form.dataset.label || "That",
      wait,
    });
    if (form.hasAttribute("data-like")) likeOptimistically(form);
    // What was typed is in the queue now. Clearing it lets the next comment be a new one, and
    // lets a second tap on Send fall to the browser's own "fill this in" check.
    if (form.hasAttribute("data-once")) form.reset();
    if (form.hasAttribute("data-plus")) { stepOptimistically(form); return; }
    if (form.dataset.leave) {
      document.getElementById(form.dataset.leave)?.classList.add("is-leaving");
      buzz(8);
    }
    if (form.dataset.write === "close" || (form.dataset.write === "wait" && !navigator.onLine)) {
      closeSheet();
      return;
    }
    if (!navigator.onLine) { toast("Saved on this device. It will sync when the connection is back."); return; }
    // This form stays on screen with what was typed in it, so it has nothing to wait for.
    if (form.dataset.write === "keep") {
      buzz(8);
      // A send waits for its answer, which replaces the form. Offline there is no answer to wait
      // for, and the token makes sending it again harmless.
      const send = form.hasAttribute("data-once") && form.querySelector('button[type="submit"]');
      if (send) { send.setAttribute("aria-busy", "true"); send.disabled = true; }
      return;
    }
    const button = form.querySelector('button[type="submit"]');
    if (button) { button.setAttribute("aria-busy", "true"); button.disabled = true; }
  });

  /* What failed, with the real reason underneath, once the page shows what the server holds. */
  function showFailure() {
    let item = null;
    try { item = JSON.parse(sessionStorage.getItem(FAILED)); } catch { item = null; }
    sessionStorage.removeItem(FAILED);
    const box = document.getElementById("write-error");
    if (!item || !box) return;
    box.querySelector("[data-what]").textContent = `Couldn't save: ${item.label}.`;
    box.querySelector("[data-why]").textContent = item.detail;
    box.hidden = false;
    box.querySelector("[data-retry]").addEventListener("click", () => {
      box.hidden = true;
      enqueue(item);
    }, { once: true });
    box.querySelector("[data-dismiss]").addEventListener("click", () => { box.hidden = true; }, { once: true });
    window.scrollTo({ top: 0 });
  }
  showFailure();

  window.addEventListener("online", () => { syncBanner(); drain(); });
  window.addEventListener("offline", syncBanner);
  window.addEventListener("pageshow", syncBanner);
  syncBanner();
  drain();

  /* Half stars. Native radios do the keyboard and screen reader work. This adds what radios
     can't do: tap the current value to clear it, and slide a finger along the row. */
  document.addEventListener("pointerdown", (e) => {
    const label = e.target.closest?.("[data-stars] .star");
    if (!label) return;
    label.dataset.wasChecked = label.querySelector("input").checked ? "1" : "";
  });
  document.addEventListener("click", (e) => {
    const input = e.target.closest?.("[data-stars] .star input");
    if (!input) return;
    const label = input.closest(".star");
    if (label.dataset.wasChecked === "1") {
      input.closest("[data-stars]").querySelector('input[value=""]').checked = true;
      label.dataset.wasChecked = "";
    }
    buzz(5);
    input.form?.dispatchEvent(new Event("stars-changed", { bubbles: true }));
  });
  document.addEventListener("pointermove", (e) => {
    if (!e.buttons && e.pointerType !== "touch") return;
    const group = e.target.closest?.("[data-stars]");
    if (!group) return;
    const under = document.elementFromPoint(e.clientX, e.clientY)?.closest?.(".star");
    if (!under || !group.contains(under)) return;
    const input = under.querySelector("input");
    if (!input.checked) {
      input.checked = true;
      // A slide chooses. It should not read as tapping the current value to clear it.
      group.querySelectorAll(".star").forEach((star) => { star.dataset.wasChecked = ""; });
      input.form?.dispatchEvent(new Event("stars-changed", { bubbles: true }));
    }
  });

  /* Log several: the stepper, and the heading and button that follow it. */
  function bulkRefresh(form) {
    const count = Number(form.elements.to.value) - Number(form.dataset.done);
    const heading = document.querySelector("[data-bulk-heading]");
    if (heading && count > 0) {
      const word = heading.dataset.word;
      heading.textContent = count === 1 ? `Log 1 ${word}` : `Log ${count} ${word}s`;
    }
    const save = form.querySelector("[data-save-label]");
    const rated = form.querySelector('[data-stars] input:checked:not([value=""])');
    if (save) save.textContent = rated ? "Save and rate" : "Save";
  }
  document.addEventListener("click", (e) => {
    const button = e.target.closest?.("[data-step]");
    if (!button) return;
    const input = button.form.elements.to;
    const next = Number(input.value || 0) + Number(button.dataset.step);
    const min = Number(input.min);
    const max = input.max ? Number(input.max) : Infinity;
    if (next < min || next > max) return;
    input.value = next;
    buzz(5);
    bulkRefresh(button.form);
  });
  document.addEventListener("input", (e) => {
    if (e.target.matches?.("form[data-bulk] input[name=to]")) bulkRefresh(e.target.form);
  });
  document.addEventListener("stars-changed", (e) => {
    if (e.target.matches?.("form[data-bulk]")) bulkRefresh(e.target);
  });
  document.body.addEventListener("htmx:afterSwap", () => {
    const form = document.querySelector("#sheet-host form[data-bulk]");
    if (form) bulkRefresh(form);
  });

  /* Episodes: a row opens in place, and fetches what it needs the first time. Closing only hides
     it, so a half-written comment is still there when it opens again. */
  document.addEventListener("click", (e) => {
    const row = e.target.closest?.("[data-ep-toggle]");
    if (!row) return;
    const open = row.getAttribute("aria-expanded") !== "true";
    const panel = document.getElementById(row.getAttribute("aria-controls"));
    row.setAttribute("aria-expanded", String(open));
    panel.hidden = !open;
    if (open && !panel.dataset.state) {
      panel.dataset.state = "loading";
      // A failed load is reported by htmx's own events, below. Its promise rejects as well.
      window.htmx?.ajax("GET", row.dataset.panel, { target: panel, swap: "innerHTML" })?.catch(() => {});
    }
  });
  document.body.addEventListener("htmx:afterRequest", (e) => {
    const panel = e.detail.target;
    if (!panel?.matches?.("[data-ep-panel]")) return;
    if (e.detail.successful) { panel.dataset.state = "loaded"; return; }
    // The toast has said why. Tapping the row again is the retry.
    delete panel.dataset.state;
    panel.hidden = true;
    document.querySelector(`[aria-controls="${panel.id}"]`)?.setAttribute("aria-expanded", "false");
  });

  /* A new season score cleared the episode scores, so open rows' stars have nothing to show. */
  document.body.addEventListener("episode-scores-cleared", () => {
    document.querySelectorAll('[data-ep-panel] [data-stars] input[value=""]').forEach((none) => { none.checked = true; });
  });

  /* A comment not saved yet: leaving the page asks first. */
  document.addEventListener("input", (e) => {
    if (e.target.matches?.(".ep__comment textarea")) e.target.form.dataset.dirty = "1";
  });
  document.addEventListener("submit", (e) => { delete e.target.dataset?.dirty; });
  window.addEventListener("beforeunload", (e) => {
    if (document.querySelector(".ep__comment[data-dirty]")) e.preventDefault();
  });

  /* Stars on an open row save themselves. A slide along them only saves where it stopped. */
  let autosaveTimer = null;
  const autosave = (e) => {
    const form = e.target.closest?.("form[data-autosave]");
    if (!form) return;
    clearTimeout(autosaveTimer);
    autosaveTimer = setTimeout(() => form.requestSubmit(), 320);
  };
  document.addEventListener("stars-changed", autosave);
  document.addEventListener("change", autosave);

  /* Library: seasons under a show. */
  document.addEventListener("click", (e) => {
    const toggle = e.target.closest?.("[data-expand]");
    if (!toggle) return;
    const open = toggle.getAttribute("aria-expanded") !== "true";
    const kids = document.getElementById(toggle.getAttribute("aria-controls"));
    toggle.setAttribute("aria-expanded", String(open));
    const other = toggle.dataset.openLabel;
    toggle.dataset.openLabel = toggle.getAttribute("aria-label");
    toggle.setAttribute("aria-label", other);
    if (kids) kids.hidden = !open;
  });

  /* Post slides. The slides scroll and snap on their own, so swiping works with no script. This
     keeps the dots in step with the scroll and lets a dot take you to its slide. */
  function syncDots(slides) {
    const dots = slides.closest("[data-post]")?.querySelectorAll("[data-dot]");
    if (!dots?.length) return;
    const index = Math.round(slides.scrollLeft / Math.max(1, slides.clientWidth));
    dots.forEach((dot, i) => dot.setAttribute("aria-pressed", i === index ? "true" : "false"));
  }
  document.addEventListener("scroll", (e) => {
    if (e.target.matches?.("[data-slides]")) syncDots(e.target);
  }, { capture: true, passive: true });
  document.addEventListener("click", (e) => {
    const dot = e.target.closest?.("[data-dot]");
    if (!dot) return;
    const slides = dot.closest("[data-post]").querySelector("[data-slides]");
    slides.scrollTo({ left: Number(dot.dataset.dot) * slides.clientWidth, behavior: reduceMotion() ? "auto" : "smooth" });
    buzz(5);
  });

  // Profile tabs and the activity Show more toggle.
  document.addEventListener("click", (e) => {
    const tab = e.target.closest?.(".me__tab");
    if (tab) {
      document.querySelectorAll(".me__tab").forEach((b) => {
        b.classList.toggle("is-active", b === tab);
        b.setAttribute("aria-selected", b === tab ? "true" : "false");
      });
      document.querySelectorAll(".me__tab-panel").forEach((p) => {
        p.classList.toggle("is-active", p.getAttribute("data-panel") === tab.getAttribute("data-tab"));
      });
      return;
    }
    const more = e.target.closest?.("[data-activity-more]");
    if (!more) return;
    const extra = more.closest(".chud-activity")?.querySelector("[data-activity-extra]");
    if (!extra) return;
    extra.hidden = !extra.hidden;
    more.textContent = extra.hidden ? "Show more" : "Show less";
  });

  /* Settings: the avatar circle opens the picture picker. */
  document.addEventListener("click", (e) => {
    const toggle = e.target.closest?.("[data-avatar-toggle]");
    if (!toggle) return;
    const picker = toggle.closest(".settings__group")?.querySelector("[data-avatar-picker]");
    if (!picker) return;
    picker.hidden = !picker.hidden;
    toggle.setAttribute("aria-expanded", picker.hidden ? "false" : "true");
  });
})();

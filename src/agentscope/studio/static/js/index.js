const dashboardTabBtn = document.getElementById("dashboard-tab-btn");
const workstationTabBtn = document.getElementById("workstation-tab-btn");
const marketTabBtn = document.getElementById("market-tab-btn");
const serverTabBtn = document.getElementById("server-tab-btn");
const navigationBar = document.getElementById("navigation-bar");
const suspendedBallDom = document.querySelector(".navbar");
let currentPageUrl = null;
let inGuidePage = true;
// When navigation bar collapsed, only when the mouse leaves the navigation bar, then navigation bar will be able to be expanded
let activeExpanded = false;

// Check if the script is already loaded
function isScriptLoaded(src) {
  if (src == "static/js/gallery.js") {
    return;
  }
  const curURL = new URL(src, window.location.href).pathname;
  return Array.from(document.scripts).some((script) => {
    try {
      const existURL = new URL(script.src).pathname;
      return existURL === curURL;
    } catch (error) {
      console.warn(
        "Error occurred when checking if the script is loaded: ",
        error
      );
      return false;
    }
  });
}

// After loading different pages, we need to call the initialization function of this page
function initializeTabPageByUrl(pageUrl) {
  switch (pageUrl) {
  case "static/html/dashboard.html":
    initializeDashboardPage();
    break;
  case "static/html/workstation_iframe.html":
    const script = document.createElement("script");
    script.src = "static/js/workstation_iframe.js";
    document.head.appendChild(script);
    break;
  case "static/html/server.html":
    initializeServerPage();
    break;
  }
}

// Loading different pages in index.html
function loadTabPage(pageUrl, javascriptUrl) {
  fetch(pageUrl)
    .then((response) => {
      if (!response.ok) {
        throw new Error("Connection error, cannot load the web page.");
      }
      return response.text();
    })
    .then((html) => {
      currentPageUrl = pageUrl;

      // Hide the sidebar for other pages except the guide page
      if (pageUrl === "static/html/index-guide.html") {
        navigationBar.classList.remove("collapsed");
        inGuidePage = true;
      } else {
        navigationBar.classList.add("collapsed");
        inGuidePage = false;
        activeExpanded = false;
      }

      // Load the page content
      document.getElementById("content").innerHTML = html;

      if (!localStorage.getItem("currentLanguage")) {
        localStorage.setItem("currentLanguage", "en");
      }
      // Load the javascript file
      if (javascriptUrl && !isScriptLoaded(javascriptUrl)) {
        const script = document.createElement("script");
        script.src = javascriptUrl;
        script.onload = function () {
          // The first time we must initialize the page within the onload function to ensure the script is loaded
          initializeTabPageByUrl(pageUrl);
        };
        document.head.appendChild(script);
      } else {
        console.log("Script already loaded for " + javascriptUrl);
        // If is not the first time, we can directly call the initialization function
        initializeTabPageByUrl(pageUrl);
      }

      // switch selected status of the tab buttons
      switch (pageUrl) {
      case "static/html/dashboard.html":
        dashboardTabBtn.classList.add("selected");
        workstationTabBtn.classList.remove("selected");
        marketTabBtn.classList.remove("selected");
        serverTabBtn.classList.remove("selected");
        break;

      case "static/html/workstation_iframe.html":
        dashboardTabBtn.classList.remove("selected");
        workstationTabBtn.classList.add("selected");
        marketTabBtn.classList.remove("selected");
        serverTabBtn.classList.remove("selected");
        break;

      case "static/html/gallery.html":
        dashboardTabBtn.classList.remove("selected");
        workstationTabBtn.classList.remove("selected");
        marketTabBtn.classList.add("selected");
        serverTabBtn.classList.remove("selected");
        break;

      case "static/html/server.html":
        dashboardTabBtn.classList.remove("selected");
        workstationTabBtn.classList.remove("selected");
        marketTabBtn.classList.remove("selected");
        serverTabBtn.classList.add("selected");
        break;
      }
    })
    .catch((error) => {
      console.error("Error encountered while loading page: ", error);
      document.getElementById("content").innerHTML =
                "<p>Loading failed.</p>" + error;
    });
}


loadTabPage("static/html/index-guide.html", null);

document.addEventListener("DOMContentLoaded", function () {
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.has("run_id")) {
    loadTabPage("static/html/dashboard.html", "static/js/dashboard.js");
  }
});

navigationBar.addEventListener("mouseenter", function () {
  if (activeExpanded) {
    navigationBar.classList.remove("collapsed");
  }
});

navigationBar.addEventListener("mouseleave", function () {
  // In guide page, the navigation bar will not be collapsed
  if (!inGuidePage) {
    // Collapse the navigation bar when the mouse leaves the navigation bar
    navigationBar.classList.add("collapsed");
    // Allow the navigation bar to be expanded when the mouse leaves the navigation bar to avoid expanding right after collapsing (when not finished collapsing yet)
    activeExpanded = true;
  }
});

class SuspensionBall {
  constructor(dom, callback = null) {
    this.callback = callback;
    this.startEvt = "";
    this.moveEvt = "";
    this.endEvt = "";
    this.drag = dom;
    this.isClick = true;
    this.disX = 0;
    this.disY = 0;
    this.left = 0;
    this.top = 0;
    this.starX = 0;
    this.starY = 0;

    // 绑定 this
    this.startFun = this.startFun.bind(this);
    this.moveFun = this.moveFun.bind(this);
    this.endFun = this.endFun.bind(this);
  }

  init() {
    this.initEvent();
  }

  initEvent() {
    if ("ontouchstart" in window) {
      this.startEvt = "touchstart";
      this.moveEvt = "touchmove";
      this.endEvt = "touchend";
    } else {
      this.startEvt = "mousedown";
      this.moveEvt = "mousemove";
      this.endEvt = "mouseup";
    }
    this.drag.addEventListener(this.startEvt, this.startFun);
  }

  startFun(e) {
    e.preventDefault();
    e = e || window.event;
    this.isClick = true;
    this.starX = e.touches ? e.touches[0].clientX : e.clientX;
    this.starY = e.touches ? e.touches[0].clientY : e.clientY;
    this.disX = this.starX - this.drag?.offsetLeft;
    this.disY = this.starY - this.drag?.offsetTop;
    document.addEventListener(this.moveEvt, this.moveFun);
    document.addEventListener(this.endEvt, this.endFun);
  }

  moveFun(e) {
    e.preventDefault();
    e = e || window.event;
    if (
      Math.abs(this.starX - (e.touches ? e.touches[0].clientX : e.clientX)) > 20 ||
            Math.abs(this.starY - (e.touches ? e.touches[0].clientY : e.clientY)) > 20
    ) {
      this.isClick = false;
    }
    this.left = (e.touches ? e.touches[0].clientX : e.clientX) - this.disX;
    this.top = (e.touches ? e.touches[0].clientY : e.clientY) - this.disY;
    if (this.left < 0) {
      this.left = 0;
    } else if (this.left > document.documentElement.clientWidth - this.drag.offsetWidth) {
      this.left = document.documentElement.clientWidth - this.drag.offsetWidth;
    }
    if (this.top < 0) {
      this.top = 0;
    } else if (this.top > document.documentElement.clientHeight - this.drag.offsetHeight) {
      this.top = document.documentElement.clientHeight - this.drag.offsetHeight;
    }
    this.drag.style.left = this.left + "px";
    this.drag.style.top = this.top + "px";
  }

  endFun(e) {
    document.removeEventListener(this.moveEvt, this.moveFun);
    document.removeEventListener(this.endEvt, this.endFun);
    if (this.isClick && this.callback) { // 点击
      this.callback();
    }
  }

  removeDrag() {
    this.drag.remove();
  }
}

const suspensionBall = new SuspensionBall(suspendedBallDom);
suspensionBall.init();

const observer = new MutationObserver((mutations) => {
  mutations.forEach((mutation) => {
    if (mutation.type === "childList") {
      debounceFun();
    }
  });
});

observer.observe(document.body, {
  childList: true,
  subtree: true,
});

const debounceFun = debounce(function refreshI18n() {
  const currentLang = getCookie("locale") || "en";
  observer.disconnect();
  $("[i18n]").i18n({
    defaultLang: currentLang,
    filePath: "../static/i18n/",
    filePrefix: "i18n_",
    fileSuffix: "",
    forever: true,
    callback: function () {
      observer.observe(document.body, {
        childList: true,
        subtree: true,
      });
    }
  });
}, 100);

document.addEventListener("DOMContentLoaded", function () {
  const currentLang = getCookie("locale") || "en";
  switch (currentLang) {
  case "en":
    document.getElementById("translate").innerText = "en";
    break;
  case "zh":
    document.getElementById("translate").innerText = "中";
    break;
  }
});

function changeLanguage() {
  const currentLang = getCookie("locale") || "en";
  switch (currentLang) {
  case "en":
    document.getElementById("translate").innerText = "中";
    localStorage.setItem("locale", "zh");
    setCookie("locale", "zh");
    break;
  case "zh":
    document.getElementById("translate").innerText = "en";
    localStorage.setItem("locale", "en");
    setCookie("locale", "en");
    break;
  }
}

function debounce(func, delay) {
  let timeout;

  return function (...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), delay);
  };
}

function getCookie(name) {
  const matches = document.cookie.match(new RegExp(
    "(?:^|; )" + name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, "\\$1") + "=([^;]*)"
  ));
  return matches ? decodeURIComponent(matches[1]) : undefined;
}

function setCookie(name, value, days) {
  let expires = "";
  if (days) {
    const date = new Date();
    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
    expires = "; expires=" + date.toUTCString();
  }
  document.cookie = name + "=" + (value || "") + expires + "; path=/";
}
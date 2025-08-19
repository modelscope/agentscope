function switchLanguage() {
    if (window.location.href.includes("zh_CN")) {
        window.location.href = "https://doc.agentscope.io";
    } else {
        window.location.href = "https://doc.agentscope.io/zh_CN";
    }
}


function switchVersion() {
    const suffix = window.location.href.includes("zh_CN") ? "/zh_CN" : "";
    window.location.href = "https://doc.agentscope.io/v0" + suffix;
}

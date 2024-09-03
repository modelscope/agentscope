/* the js code here is referenced from WebVoyager and tarsier
WebVoyager js code: https://github.com/MinorJerry/WebVoyager/blob/main/utils.py
tarsier js code: https://github.com/reworkd/tarsier/blob/main/tarsier/tag_utils.ts
*/

//Get the visible interactive elements on the current web page
function getInteractiveElements() {
    let allElements = Array.prototype.slice.call(
        document.querySelectorAll('*')
    )

    var items = allElements.map(function(element) {
        var vw = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);
        var vh = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);

        var elementClassName = (typeof element.className === 'string' ? element.className : '').replace(/\s+/g, '.');

        var rects = [...element.getClientRects()].filter(bb => {
            var center_x = bb.left + bb.width / 2;
            var center_y = bb.top + bb.height / 2;
            var elAtCenter = document.elementFromPoint(center_x, center_y);
            return elAtCenter === element || element.contains(elAtCenter)
        }).map(bb => {
            const rect = {
                left: Math.max(0, bb.left),
                top: Math.max(0, bb.top),
                right: Math.min(vw, bb.right),
                bottom: Math.min(vh, bb.bottom)
            };
            return {
                ...rect,
                width: rect.right - rect.left,
                height: rect.bottom - rect.top
            };
        });
        var area = rects.reduce((acc, rect) => acc + rect.width * rect.height, 0);
        return {
            element: element,
            include:
                (element.tagName === "INPUT" || element.tagName === "TEXTAREA" || element.tagName === "SELECT") ||
                (element.tagName === "BUTTON" || element.tagName === "A" || (element.onclick != null) || window.getComputedStyle(element).cursor == "pointer") ||
                (element.tagName === "IFRAME" || element.tagName === "VIDEO" || element.tagName === "LI" || element.tagName === "TD" || element.tagName === "OPTION"),
            area,
            rects,
            text: element.textContent.trim().replace(/\s{2,}/g, ' ')
        };
    }).filter(item =>
        item.include && (item.area >= 20)
    );

    // Filter out buttons and elements that are contained by buttons or spans
    const buttons = Array.from(document.querySelectorAll('button, a, input[type="button"], div[role="button"]' ));
    items = items.filter(x => !buttons.some(y => items.some(z => z.element === y) && y.contains(x.element) && !(x.element === y)));
    items = items.filter(x =>
        !(x.element.parentNode &&
        x.element.parentNode.tagName === 'SPAN' &&
        x.element.parentNode.children.length === 1 &&
        x.element.parentNode.getAttribute('role') &&
        items.some(y => y.element === x.element.parentNode)));
    items = items.filter(x => !items.some(y => x.element.contains(y.element) && !(x == y)));

    return items;
}

// Set interactive marks on the current web page
function setInteractiveMarks() {
    var items = getInteractiveElements();

    // Init an array to record the item information
    var itemsInfo = [];
    items.forEach(function(item, index) {
        item.rects.forEach((bbox) => {
            // Create a mark element for each interactive element
            let newElement = document.createElement("div");
            newElement.classList.add("agentscope-interactive-mark")

            // border
            var borderColor = "#000000";
            newElement.style.outline = `2px dashed ${borderColor}`;
            newElement.style.position = "fixed";
            newElement.style.left = bbox.left + "px";
            newElement.style.top = bbox.top + "px";
            newElement.style.width = bbox.width + "px";
            newElement.style.height = bbox.height + "px";
            newElement.style.pointerEvents = "none";
            newElement.style.boxSizing = "border-box";
            newElement.style.zIndex = 2147483647;

            // index label
            var label = document.createElement("span");
            label.textContent = index;
            label.style.position = "absolute";
            label.style.top = Math.max(-19, -bbox.top) + "px";
            label.style.left = Math.min(Math.floor(bbox.width / 5), 2) + "px";
            label.style.background = borderColor;
            label.style.color = "white";
            label.style.padding = "2px 4px";
            label.style.fontSize = "12px";
            label.style.borderRadius = "2px";
            newElement.appendChild(label);

            document.body.appendChild(newElement);
        });

        // Record the item information
        itemsInfo[index] = getElementInfo(index, item.element);
    });
    return {items, itemsInfo};
}
// <a hre="
function getElementInfo(index, element) {
    const rect = element.getBoundingClientRect();
    return {
        html: element.outerHTML,
        tag_name: element.tagName.toLowerCase(),
        node_name: element.nodeName.toLowerCase(),
        node_value: element.nodeValue,
        type: element.getAttribute('type') ? element.getAttribute('type').toLowerCase() : null,
        aria_label: element.getAttribute('aria-label') ? element.getAttribute('aria-label').toLowerCase() : null,
        is_clickable: !!element.onclick || (element.tagName === 'A' && element.href),
        meta_data: Array.from(element.attributes).map(attr => `${attr.name}="${attr.value}"`),
        inner_text: element.innerText || element.textContent || '',
        origin_x: rect.x,
        origin_y: rect.y,
        width: rect.width,
        height: rect.height
    };
}

// Remove all interactive marks by class name
function removeInteractiveMarks() {
    var marks = document.getElementsByClassName("agentscope-interactive-mark");
    while (marks.length > 0) {
        marks[0].parentNode.removeChild(marks[0]);
    }
}
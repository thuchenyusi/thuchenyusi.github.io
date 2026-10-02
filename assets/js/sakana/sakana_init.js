/*
 * Sakana 小组件初始化
 * 桌面端（> 849px）：保持原样，右下角常驻展示
 * 移动端（<= 849px）：默认收纳为左下角浮动按钮，点击展开/收起，
 * 展开时点击组件外部区域自动收起，并用 localStorage 记住用户选择
 */
(function () {
    var template = document.getElementById('sakana-template');
    document.body.appendChild(template.content.cloneNode(true));
    template.remove();
    var MOBILE_QUERY = '(max-width: 849px)';
    var STORAGE_KEY = 'sakana:expanded';
    var EXPANDED_CLASS = 'sakana-expanded';

    var mql = window.matchMedia(MOBILE_QUERY);
    var root = document.documentElement;
    var box = document.querySelector('.sakana-box');
    var toggle = document.getElementById('sakana-toggle');
    var initialized = false;

    function initSakana() {
        if (initialized) {
            return;
        }
        initialized = true;
        Sakana.init({
            el: '.sakana-box',              // 启动元素 node 或 选择器
            scale: mql.matches ? 0.5 : 0.65, // 移动端缩小，减少遮挡
            canSwitchCharacter: true,       // 允许换角色
        });
    }

    function saveExpanded(on) {
        try {
            localStorage.setItem(STORAGE_KEY, on ? '1' : '0');
        } catch (e) {
            /* 隐私模式等场景下无法写入，忽略 */
        }
    }

    function setExpanded(on) {
        root.classList.toggle(EXPANDED_CLASS, on);
        toggle.querySelector('i').className = on ? 'fas fa-times' : 'fas fa-fish';
        toggle.setAttribute('aria-expanded', on ? 'true' : 'false');
        saveExpanded(on);
    }

    function isExpanded() {
        return root.classList.contains(EXPANDED_CLASS);
    }

    if (!mql.matches) {
        // 桌面端：立即初始化
        initSakana();
    } else {
        // 移动端：恢复上次的展开状态（默认收起，且不初始化以节省资源）
        var saved = null;
        try {
            saved = localStorage.getItem(STORAGE_KEY);
        } catch (e) {
            /* 无法读取时视为默认收起 */
        }
        if (saved === '1') {
            initSakana();
            setExpanded(true);
        }
    }

    toggle.addEventListener('click', function () {
        if (!initialized) {
            initSakana(); // 移动端首次展开时才初始化
        }
        setExpanded(!isExpanded());
    });

    // 展开状态下点击组件外部区域则收起
    document.addEventListener('click', function (event) {
        if (!mql.matches || !isExpanded()) {
            return;
        }
        if (box.contains(event.target) || toggle.contains(event.target)) {
            return;
        }
        setExpanded(false);
    });

    // 跨断点变化（如旋转屏幕、拖动窗口）时，切到桌面端要保证组件已初始化
    var onBreakpointChange = function (event) {
        if (!event.matches) {
            initSakana();
        }
    };
    if (mql.addEventListener) {
        mql.addEventListener('change', onBreakpointChange);
    } else if (mql.addListener) {
        mql.addListener(onBreakpointChange); // 兼容旧版 Safari
    }
})();

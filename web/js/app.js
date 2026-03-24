const VIRTUAL_UNARCHIVED_SEGMENT = '__virtual_unarchived__';
const UNARCHIVED_LABEL = '未归档';

const homeView = document.getElementById('home-view');
const browseView = document.getElementById('browse-view');
const listView = document.getElementById('list-view');
const postView = document.getElementById('post-view');
const categoriesContainer = document.getElementById('categories-container');
const recentPostsContainer = document.getElementById('recent-posts-container');
const postsContainer = document.getElementById('posts-container');
const listBreadcrumb = document.getElementById('list-breadcrumb');
const postBreadcrumb = document.getElementById('post-breadcrumb');
const browseBreadcrumb = document.getElementById('browse-breadcrumb');
const listHeadingTitle = document.getElementById('list-heading-title');
const browseHeadingTitle = document.getElementById('browse-heading-title');
const browseFolders = document.getElementById('browse-folders');
const browseFiles = document.getElementById('browse-files');
const renameBtn = document.getElementById('rename-btn');
const viewTitle = document.getElementById('view-title');
const viewDate = document.getElementById('view-date');
const viewContent = document.getElementById('view-content');
const progressBar = document.getElementById('progress-bar');
const siteHeader = document.getElementById('site-header');

const passwordModal = document.getElementById('password-modal');
const modalPassword = document.getElementById('modal-password');
const modalError = document.getElementById('modal-error');
const modalTitle = document.getElementById('modal-title');
let pendingCategory = '';

const renameModal = document.getElementById('rename-modal');
const renameInput = document.getElementById('rename-input');
const renamePassword = document.getElementById('rename-password');
const renameError = document.getElementById('rename-error');
let renamePath = '';
let currentBrowsePath = '';
let activeBrowseRequest = '';

const SVG_ICONS = {
    edit: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>`,
    code: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>`,
    book: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>`,
    sun: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>`,
    heart: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>`,
    plane: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 8l4 4-4 4"/><path d="M3 12h18"/><path d="M7 8l-4 4 4 4"/></svg>`,
    folder: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>`,
    file: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>`,
    lock: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>`,
};

const CATEGORY_ICON_MAP = {
    '技术笔记': 'code',
    '日常生活': 'sun',
    '读书笔记': 'book',
    '个人心得': 'heart',
    '旅行日记': 'plane',
    '未归档': 'file',
    '编程教学': 'code',
    '项目文档': 'file',
    '课程作业': 'book',
    '打字练习': 'edit',
    '日记': 'heart',
    '算法竞赛': 'code',
    'C++项目': 'code',
    '题目笔记': 'book',
};

function getCatIcon(name, fallback = 'folder') {
    const key = CATEGORY_ICON_MAP[name] || fallback;
    return SVG_ICONS[key] || SVG_ICONS.folder;
}

function isVirtualUnarchivedPath(path) {
    const parts = path.split('/').filter(Boolean);
    return parts.length > 0 && parts[parts.length - 1] === VIRTUAL_UNARCHIVED_SEGMENT;
}

function getPathLabel(part) {
    return part === VIRTUAL_UNARCHIVED_SEGMENT ? UNARCHIVED_LABEL : part;
}

function getBrowseHash(path) {
    return `#browse/${encodeURIComponent(path)}`;
}

function navigateToBrowse(path) {
    const targetHash = getBrowseHash(path);
    if (window.location.hash !== targetHash) {
        window.location.hash = targetHash;
    }

    setTimeout(() => {
        if (
            window.location.hash === targetHash
            && currentBrowsePath !== path
            && activeBrowseRequest !== path
        ) {
            showSection('browse');
            void loadBrowseView(path);
        }
    }, 0);
}

function routeLegacyCategory(category) {
    if (category === '_uncategorized') {
        navigateToBrowse(VIRTUAL_UNARCHIVED_SEGMENT);
        return;
    }
    navigateToBrowse(category);
}

function buildBreadcrumb(path, currentLabel = '') {
    const parts = path.split('/').filter(Boolean);
    let crumbs = `<a href="#home">首页</a>`;
    let accumulated = '';

    for (let i = 0; i < parts.length; i++) {
        accumulated += (i === 0 ? '' : '/') + parts[i];
        const label = i === parts.length - 1
            ? (currentLabel || getPathLabel(parts[i]))
            : getPathLabel(parts[i]);
        if (i < parts.length - 1) {
            crumbs += `<span class="sep">›</span><a href="${getBrowseHash(accumulated)}">${label}</a>`;
        } else {
            crumbs += `<span class="sep">›</span><span>${label}</span>`;
        }
    }

    return crumbs;
}

function showSection(name) {
    const sections = {
        home: homeView,
        browse: browseView,
        list: listView,
        post: postView,
    };

    Object.entries(sections).forEach(([key, element]) => {
        if (key === name) {
            element.style.display = 'block';
            element.classList.remove('fade-in');
            void element.offsetWidth;
            element.classList.add('fade-in');
        } else {
            element.style.display = 'none';
        }
    });

    progressBar.classList.toggle('visible', name === 'post');
}

async function router() {
    const hash = window.location.hash || '#home';

    if (hash === '#home' || hash === '') {
        showSection('home');
        await loadHomePage();
        return;
    }

    if (hash === '#browse') {
        location.hash = '#home';
        return;
    }

    if (hash.startsWith('#browse/')) {
        const path = decodeURIComponent(hash.replace('#browse/', ''));
        showSection('browse');
        await loadBrowseView(path);
        return;
    }

    if (hash.startsWith('#category/')) {
        const category = decodeURIComponent(hash.replace('#category/', ''));
        routeLegacyCategory(category);
        return;
    }

    if (hash.startsWith('#post/')) {
        const slug = decodeURIComponent(hash.replace('#post/', ''));
        showSection('post');
        await loadPostDetail(slug);
    }
}

async function loadHomePage() {
    await Promise.all([loadStats(), loadRecentPosts(), loadCategories()]);
}

async function loadStats() {
    try {
        const res = await fetch('/api/stats');
        const stats = await res.json();
        document.getElementById('stat-posts').textContent = stats.total_posts;
        document.getElementById('stat-cats').textContent = stats.total_categories;
        document.getElementById('stat-updated').textContent = stats.last_updated;
    } catch (error) {
        console.error('统计加载失败', error);
    }
}

async function loadRecentPosts() {
    try {
        const res = await fetch('/api/posts');
        const posts = await res.json();
        const recentPosts = posts.slice(0, 4);
        if (recentPosts.length === 0) {
            recentPostsContainer.innerHTML = '<p class="empty-state">暂无文章</p>';
            return;
        }

        recentPostsContainer.innerHTML = recentPosts.map((post) => `
            <div class="recent-card" data-slug="${encodeURIComponent(post.slug)}">
                <div class="rc-date">${post.date}</div>
                <div class="rc-title">${post.title}</div>
                <span class="rc-cat">${post.category}</span>
            </div>
        `).join('');

        recentPostsContainer.querySelectorAll('.recent-card').forEach((card) => {
            card.addEventListener('click', () => {
                location.hash = `#post/${card.dataset.slug}`;
            });
        });
    } catch (error) {
        recentPostsContainer.innerHTML = '<p class="empty-state">加载失败</p>';
    }
}

async function loadCategories() {
    try {
        const res = await fetch('/api/categories');
        const categories = await res.json();
        if (categories.length === 0) {
            categoriesContainer.innerHTML = '<p class="empty-state">暂无分类</p>';
            return;
        }

        categoriesContainer.innerHTML = categories.map((category) => `
            <div class="category-card" data-slug="${category.slug}" data-locked="${category.locked}">
                <div class="cat-icon">${getCatIcon(category.name)}</div>
                <div class="cat-info">
                    <div class="cat-name">${category.name}</div>
                    <div class="cat-count">${category.count} 篇</div>
                </div>
                ${category.locked ? `<div class="lock-badge">${SVG_ICONS.lock}</div>` : ''}
            </div>
        `).join('');

        categoriesContainer.querySelectorAll('.category-card').forEach((card) => {
            card.addEventListener('click', () => {
                onCategoryClick(card.dataset.slug, card.dataset.locked === 'true');
            });
        });
    } catch (error) {
        categoriesContainer.innerHTML = '<p class="empty-state">加载失败</p>';
    }
}

function onCategoryClick(slug, locked) {
    if (locked) {
        pendingCategory = slug;
        modalTitle.textContent = `“${slug}”已加密`;
        modalPassword.value = '';
        modalError.textContent = '';
        passwordModal.classList.add('active');
        setTimeout(() => modalPassword.focus(), 100);
        return;
    }

    if (slug === '_uncategorized') {
        navigateToBrowse(VIRTUAL_UNARCHIVED_SEGMENT);
        return;
    }

    navigateToBrowse(slug);
}

function closeModal() {
    passwordModal.classList.remove('active');
    pendingCategory = '';
}

async function submitPassword() {
    const password = modalPassword.value.trim();
    if (!password) {
        modalError.textContent = '请输入密码';
        return;
    }

    try {
        const res = await fetch('/api/verify-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category: pendingCategory, password }),
        });

        if (res.ok) {
            const targetCategory = pendingCategory;
            closeModal();
            navigateToBrowse(targetCategory);
            return;
        }

        modalError.textContent = '密码错误，请重试';
        modalPassword.value = '';
        modalPassword.focus();
    } catch (error) {
        modalError.textContent = '验证失败，请稍后重试';
    }
}

async function loadBrowseView(path) {
    activeBrowseRequest = path;
    try {
        const res = await fetch(`/api/browse?path=${encodeURIComponent(path)}`);
        if (res.status === 403) {
            location.hash = '#home';
            const category = path.split('/').filter(Boolean).find((part) => part !== VIRTUAL_UNARCHIVED_SEGMENT);
            if (category) {
                setTimeout(() => onCategoryClick(category, true), 200);
            }
            return;
        }
        if (!res.ok) {
            throw new Error('加载失败');
        }

        const data = await res.json();
        currentBrowsePath = data.path;
        browseBreadcrumb.innerHTML = buildBreadcrumb(path, data.display_name);
        browseHeadingTitle.textContent = data.display_name || '浏览';

        renamePath = path;
        renameBtn.style.display = path && !isVirtualUnarchivedPath(path) ? 'inline-flex' : 'none';

        if (data.folders.length > 0) {
            browseFolders.innerHTML = `
                <div class="category-grid">
                    ${data.folders.map((folder) => {
                        const isVirtualFolder = isVirtualUnarchivedPath(folder.path);
                        const icon = isVirtualFolder ? SVG_ICONS.file : SVG_ICONS.folder;
                        return `
                            <div
                                class="category-card"
                                data-path="${encodeURIComponent(folder.path)}"
                                data-name="${folder.name}"
                                data-locked="${folder.locked}"
                            >
                                <div class="cat-icon">${icon}</div>
                                <div class="cat-info">
                                    <div class="cat-name">${folder.display_name}</div>
                                    <div class="cat-count">${folder.count} 篇</div>
                                </div>
                                ${folder.locked ? `<div class="lock-badge">${SVG_ICONS.lock}</div>` : ''}
                            </div>
                        `;
                    }).join('')}
                </div>
            `;

            browseFolders.querySelectorAll('.category-card').forEach((card) => {
                card.addEventListener('click', () => {
                    if (card.dataset.locked === 'true') {
                        onCategoryClick(card.dataset.name, true);
                        return;
                    }
                    navigateToBrowse(decodeURIComponent(card.dataset.path));
                });
            });
        } else {
            browseFolders.innerHTML = '';
        }

        if (data.files.length > 0) {
            let html = data.files.map((file) => `
                <div class="post-list-item" data-slug="${encodeURIComponent(file.slug)}">
                    <div class="post-meta"><span class="post-date">${file.date}</span></div>
                    <h2 class="post-title">${file.title}</h2>
                    <p class="post-summary">${file.summary}</p>
                </div>
            `).join('');

            if (data.has_more) {
                html += `<p class="empty-state">共 ${data.total_files} 个文件，当前显示前 ${data.files.length} 个</p>`;
            }

            browseFiles.innerHTML = html;
            browseFiles.querySelectorAll('.post-list-item').forEach((item) => {
                item.addEventListener('click', () => {
                    location.hash = `#post/${item.dataset.slug}`;
                });
            });
        } else if (data.folders.length === 0) {
            browseFiles.innerHTML = '<p class="empty-state">该目录下暂无内容</p>';
        } else {
            browseFiles.innerHTML = '';
        }
    } catch (error) {
        browseBreadcrumb.innerHTML = buildBreadcrumb(path, getPathLabel(path.split('/').filter(Boolean).pop() || ''));
        browseHeadingTitle.textContent = getPathLabel(path.split('/').filter(Boolean).pop() || '浏览');
        browseFolders.innerHTML = '';
        browseFiles.innerHTML = '<p class="empty-state">加载失败</p>';
    } finally {
        if (activeBrowseRequest === path) {
            activeBrowseRequest = '';
        }
    }
}

renameBtn.addEventListener('click', () => {
    renameInput.value = browseHeadingTitle.textContent;
    renamePassword.value = '';
    renameError.textContent = '';
    renameModal.classList.add('active');
    setTimeout(() => renameInput.focus(), 100);
});

function closeRenameModal() {
    renameModal.classList.remove('active');
}

async function submitRename() {
    const newName = renameInput.value.trim();
    const password = renamePassword.value.trim();

    if (!newName) {
        renameError.textContent = '请输入新名称';
        return;
    }
    if (!password) {
        renameError.textContent = '请输入管理员密码';
        return;
    }

    try {
        const res = await fetch('/api/admin/rename-category', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password, path: renamePath, new_name: newName }),
        });

        if (res.ok) {
            closeRenameModal();
            await loadBrowseView(renamePath);
            return;
        }

        const data = await res.json();
        renameError.textContent = data.detail || '操作失败';
    } catch (error) {
        renameError.textContent = '请求失败，请稍后重试';
    }
}

async function loadPostsByCategory(category) {
    const displayName = category === '_uncategorized' ? UNARCHIVED_LABEL : category;
    listBreadcrumb.innerHTML = `<a href="#home">首页</a><span class="sep">›</span><span>${displayName}</span>`;
    listHeadingTitle.textContent = displayName;

    try {
        const res = await fetch(`/api/posts?category=${encodeURIComponent(category)}`);
        if (res.status === 403) {
            location.hash = '#home';
            setTimeout(() => onCategoryClick(category, true), 200);
            return;
        }

        const posts = await res.json();
        if (posts.length === 0) {
            postsContainer.innerHTML = '<p class="empty-state">该分类下暂无文章</p>';
            return;
        }

        postsContainer.innerHTML = posts.map((post) => `
            <div class="post-list-item" data-slug="${encodeURIComponent(post.slug)}">
                <div class="post-meta"><span class="post-date">${post.date}</span></div>
                <h2 class="post-title">${post.title}</h2>
                <p class="post-summary">${post.summary}</p>
            </div>
        `).join('');

        postsContainer.querySelectorAll('.post-list-item').forEach((item) => {
            item.addEventListener('click', () => {
                location.hash = `#post/${item.dataset.slug}`;
            });
        });
    } catch (error) {
        postsContainer.innerHTML = '<p class="empty-state">加载失败</p>';
    }
}

function buildPostBreadcrumb(slug) {
    const parts = slug.split('/').filter(Boolean);
    if (parts.length <= 1) {
        return `
            <a href="#home">首页</a>
            <span class="sep">›</span>
            <a href="${getBrowseHash(VIRTUAL_UNARCHIVED_SEGMENT)}">${UNARCHIVED_LABEL}</a>
            <span class="sep">›</span>
            <span>正文</span>
        `;
    }

    let crumbs = `<a href="#home">首页</a>`;
    let accumulated = '';
    for (let i = 0; i < parts.length - 1; i++) {
        accumulated += (i === 0 ? '' : '/') + parts[i];
        crumbs += `<span class="sep">›</span><a href="${getBrowseHash(accumulated)}">${getPathLabel(parts[i])}</a>`;
    }
    crumbs += `<span class="sep">›</span><span>正文</span>`;
    return crumbs;
}

function decorateCodeBlocks() {
    if (!window.hljs) {
        return;
    }

    const blocks = document.querySelectorAll('.markdown-body pre code');
    blocks.forEach((block) => {
        hljs.highlightElement(block);

        const pre = block.parentElement;
        if (pre.querySelector('.code-copy-btn')) {
            return;
        }

        const langClass = Array.from(block.classList).find((name) => name.startsWith('language-'));
        if (langClass) {
            const badge = document.createElement('span');
            badge.className = 'code-lang-badge';
            badge.innerText = langClass.replace('language-', '');
            pre.appendChild(badge);
        }

        const button = document.createElement('button');
        button.className = 'code-copy-btn';
        button.innerText = 'Copy';
        pre.appendChild(button);

        button.addEventListener('click', async () => {
            try {
                if (navigator.clipboard && window.isSecureContext) {
                    await navigator.clipboard.writeText(block.innerText);
                } else {
                    const textArea = document.createElement('textarea');
                    textArea.value = block.innerText;
                    textArea.style.position = 'fixed';
                    textArea.style.left = '-999999px';
                    textArea.style.top = '-999999px';
                    document.body.appendChild(textArea);
                    textArea.focus();
                    textArea.select();
                    document.execCommand('copy');
                    textArea.remove();
                }

                button.innerText = 'Copied!';
                button.style.color = '#fff';
                button.style.background = 'rgba(39, 201, 63, 0.4)';
                setTimeout(() => {
                    button.innerText = 'Copy';
                    button.style.color = '';
                    button.style.background = '';
                }, 2000);
            } catch (error) {
                console.error('复制失败', error);
                button.innerText = 'Error';
                setTimeout(() => {
                    button.innerText = 'Copy';
                }, 2000);
            }
        });
    });
}

async function loadPostDetail(slug) {
    window.scrollTo({ top: 0, behavior: 'auto' });
    viewTitle.textContent = '';
    viewDate.textContent = '';
    viewContent.innerHTML = '<p class="loading">加载中...</p>';
    postBreadcrumb.innerHTML = buildPostBreadcrumb(slug);

    const parts = slug.split('/').filter(Boolean);

    try {
        const res = await fetch(`/api/posts/${encodeURIComponent(slug)}`);
        if (res.status === 403) {
            location.hash = '#home';
            const category = parts.find((part) => part !== VIRTUAL_UNARCHIVED_SEGMENT);
            if (category) {
                setTimeout(() => onCategoryClick(category, true), 200);
            }
            return;
        }
        if (!res.ok) {
            throw new Error('找不到该文章');
        }

        const post = await res.json();
        viewTitle.textContent = post.title;
        viewDate.textContent = post.date;
        viewContent.innerHTML = post.content;

        if (window.renderMathInElement) {
            renderMathInElement(viewContent, {
                delimiters: [
                    { left: '$$', right: '$$', display: true },
                    { left: '$', right: '$', display: false },
                ],
                throwOnError: false,
            });
        }

        requestAnimationFrame(() => {
            decorateCodeBlocks();
        });
    } catch (error) {
        viewTitle.textContent = '出错了';
        viewContent.innerHTML = `<p class="empty-state">${error.message}</p>`;
    }
}

function updateProgressBar() {
    if (postView.style.display !== 'block') {
        return;
    }
    const totalHeight = document.documentElement.scrollHeight - window.innerHeight;
    progressBar.style.width = totalHeight > 0
        ? `${Math.min((window.scrollY / totalHeight) * 100, 100)}%`
        : '0%';
}

modalPassword.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
        submitPassword();
    }
});

passwordModal.addEventListener('click', (event) => {
    if (event.target === event.currentTarget) {
        closeModal();
    }
});

renameInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
        renamePassword.focus();
    }
});

renamePassword.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
        submitRename();
    }
});

renameModal.addEventListener('click', (event) => {
    if (event.target === event.currentTarget) {
        closeRenameModal();
    }
});

window.addEventListener('scroll', () => {
    updateProgressBar();
    siteHeader.classList.toggle('scrolled', window.scrollY > 10);
}, { passive: true });

window.addEventListener('hashchange', router);
window.addEventListener('load', router);

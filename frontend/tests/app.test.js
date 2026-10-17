import { describe, it, before, after, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import { createServer } from 'vite';

let vite;
let apiModule;
let CVComparison;
let ScoreGauge;
let LoadingSpinner;
let Landing;

// Minimal browser storage & location shim for interceptor tests
function createStorageMock() {
  const store = new Map();
  return {
    getItem: (k) => (store.has(k) ? store.get(k) : null),
    setItem: (k, v) => store.set(k, String(v)),
    removeItem: (k) => store.delete(k),
    clear: () => store.clear(),
  };
}

describe('CareerAI Frontend Suite', () => {
  before(async () => {
    globalThis.localStorage = createStorageMock();
    globalThis.window = {
      location: { pathname: '/dashboard', href: '/dashboard' },
    };

    vite = await createServer({
      root: process.cwd(),
      server: { middlewareMode: true },
      appType: 'custom',
      logLevel: 'silent',
    });

    apiModule = await vite.ssrLoadModule('/src/services/api.js');
    CVComparison = (await vite.ssrLoadModule('/src/components/CVComparison.jsx')).default;
    ScoreGauge = (await vite.ssrLoadModule('/src/components/ScoreGauge.jsx')).default;
    LoadingSpinner = (await vite.ssrLoadModule('/src/components/LoadingSpinner.jsx')).default;
    Landing = (await vite.ssrLoadModule('/src/pages/Landing.jsx')).default;
  });

  after(async () => {
    if (vite) {
      await vite.close();
    }
  });

  beforeEach(() => {
    globalThis.localStorage.clear();
    globalThis.window.location = { pathname: '/dashboard', href: '/dashboard' };
  });

  it('attaches Bearer token in request interceptor when token exists in localStorage', () => {
    const api = apiModule.default;
    const reqHandler = api.interceptors.request.handlers[0].fulfilled;

    const configWithoutToken = reqHandler({ headers: {} });
    assert.equal(configWithoutToken.headers.Authorization, undefined);

    globalThis.localStorage.setItem('token', 'jwt-test-token-123');
    const configWithToken = reqHandler({ headers: {} });
    assert.equal(configWithToken.headers.Authorization, 'Bearer jwt-test-token-123');
  });

  it('does not redirect or clear storage on 401 from /api/auth/login (401 loop guard)', async () => {
    const api = apiModule.default;
    const errHandler = api.interceptors.response.handlers[0].rejected;

    globalThis.localStorage.setItem('token', 'existing-token');
    globalThis.window.location = { pathname: '/login', href: '/login' };

    const loginErr = {
      response: { status: 401 },
      config: { url: '/api/auth/login' },
    };

    await assert.rejects(() => errHandler(loginErr));
    assert.equal(globalThis.localStorage.getItem('token'), 'existing-token');
    assert.equal(globalThis.window.location.href, '/login');
  });

  it('clears storage and redirects to /login on 401 from protected endpoints', async () => {
    const api = apiModule.default;
    const errHandler = api.interceptors.response.handlers[0].rejected;

    globalThis.localStorage.setItem('token', 'expired-token');
    globalThis.localStorage.setItem('user', '{"id":1}');
    globalThis.window.location = { pathname: '/cv', href: '/cv' };

    const protectedErr = {
      response: { status: 401 },
      config: { url: '/api/cv/history' },
    };

    await assert.rejects(() => errHandler(protectedErr));
    assert.equal(globalThis.localStorage.getItem('token'), null);
    assert.equal(globalThis.localStorage.getItem('user'), null);
    assert.equal(globalThis.window.location.href, '/login');
  });

  it('renders CVComparison placeholders and escapes HTML content safely', () => {
    const emptyHtml = renderToStaticMarkup(
      React.createElement(CVComparison, { original: '', optimized: '' })
    );
    assert.match(emptyHtml, /No text extracted yet\./);
    assert.match(emptyHtml, /Run optimization to see results\./);

    const populatedHtml = renderToStaticMarkup(
      React.createElement(CVComparison, {
        original: 'Original Engineer <script>alert(1)</script>',
        optimized: 'Optimized Senior Engineer',
      })
    );
    assert.match(populatedHtml, /Original Engineer &lt;script&gt;alert\(1\)&lt;\/script&gt;/);
    assert.match(populatedHtml, /Optimized Senior Engineer/);
  });

  it('renders ScoreGauge SVG and custom label', () => {
    const html = renderToStaticMarkup(
      React.createElement(ScoreGauge, { score: 88, label: 'Overall Score' })
    );
    assert.match(html, /Overall Score/);
    assert.match(html, /\/100/);
    assert.match(html, /<svg/);
  });

  it('renders LoadingSpinner with custom text', () => {
    const html = renderToStaticMarkup(
      React.createElement(LoadingSpinner, { size: 'md', text: 'Analyzing CV…' })
    );
    assert.match(html, /Analyzing CV…/);
  });

  it('renders Landing page with navigation links inside MemoryRouter', () => {
    const html = renderToStaticMarkup(
      React.createElement(MemoryRouter, null, React.createElement(Landing))
    );
    assert.match(html, /href="\/login"/);
    assert.match(html, /href="\/register"/);
  });
});

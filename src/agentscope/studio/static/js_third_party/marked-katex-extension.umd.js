(function (global, factory) {
    typeof exports === 'object' && typeof module !== 'undefined' ? module.exports = factory(require('katex')) :
    typeof define === 'function' && define.amd ? define(['katex'], factory) :
    (global = typeof globalThis !== 'undefined' ? globalThis : global || self, global.markedKatex = factory(global.katex));
  })(this, (function (katex) { 'use strict';

    const inlineRule = /^(\${1,2})(?!\$)((?:\\.|[^\\\n])*?(?:\\.|[^\\\n\$]))\1(?=[\s?!\.,:？！。，：]|$)/;
    const blockRule = /^(\${1,2})\n((?:\\[^]|[^\\])+?)\n\1(?:\n|$)/;

    function index(options = {}) {
      return {
        extensions: [
          inlineKatex(options, createRenderer(options, false)),
          blockKatex(options, createRenderer(options, true))
        ]
      };
    }

    function createRenderer(options, newlineAfter) {
      return (token) => katex.renderToString(token.text, { ...options, displayMode: token.displayMode }) + (newlineAfter ? '\n' : '');
    }

    function inlineKatex(options, renderer) {
      return {
        name: 'inlineKatex',
        level: 'inline',
        start(src) {
          let index;
          let indexSrc = src;

          while (indexSrc) {
            index = indexSrc.indexOf('$');
            if (index === -1) {
              return;
            }

            if (index === 0 || indexSrc.charAt(index - 1) === ' ') {
              const possibleKatex = indexSrc.substring(index);

              if (possibleKatex.match(inlineRule)) {
                return index;
              }
            }

            indexSrc = indexSrc.substring(index + 1).replace(/^\$+/, '');
          }
        },
        tokenizer(src, tokens) {
          const match = src.match(inlineRule);
          if (match) {
            return {
              type: 'inlineKatex',
              raw: match[0],
              text: match[2].trim(),
              displayMode: match[1].length === 2
            };
          }
        },
        renderer
      };
    }

    function blockKatex(options, renderer) {
      return {
        name: 'blockKatex',
        level: 'block',
        tokenizer(src, tokens) {
          const match = src.match(blockRule);
          if (match) {
            return {
              type: 'blockKatex',
              raw: match[0],
              text: match[2].trim(),
              displayMode: match[1].length === 2
            };
          }
        },
        renderer
      };
    }

    return index;

  }));

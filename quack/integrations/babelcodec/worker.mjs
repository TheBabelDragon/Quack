#!/usr/bin/env node
/**
 * Quack \u2194 BabelCodec JSON-lines worker (quack.babelcodec.v1)
 * stdin: one JSON request; stdout: one JSON response; stderr: diagnostics
 * Env: BABELCODEC_ROOT = absolute path to BabelCodec checkout
 */
import { pathToFileURL } from 'node:url';
import path from 'node:path';
import fs from 'node:fs';
import process from 'node:process';

const CONTRACT = 'quack.babelcodec.v1';
const ALLOWED = new Set([
  'health',
  'validate_feature_vector',
  'canonicalize',
  'content_hash',
  'validate_event',
]);
const MIN_VERSION = [0, 12, 1];

function fail(id, code, message) {
  process.stdout.write(JSON.stringify({
    contract: CONTRACT, id: id ?? null, ok: false, error: { code, message },
  }) + '\n');
  process.exit(1);
}

function ok(id, result) {
  process.stdout.write(JSON.stringify({
    contract: CONTRACT, id: id ?? null, ok: true, result,
  }) + '\n');
}

function parseVersion(v) {
  const m = String(v || '').match(/(\d+)\.(\d+)\.(\d+)/);
  return m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null;
}

function versionGte(a, b) {
  for (let i = 0; i < 3; i++) {
    if (a[i] > b[i]) return true;
    if (a[i] < b[i]) return false;
  }
  return true;
}

async function loadNeural(root) {
  const pkgPath = path.join(root, 'package.json');
  if (!fs.existsSync(pkgPath)) {
    throw Object.assign(new Error(`BABELCODEC_ROOT has no package.json: ${root}`), {
      code: 'BABELCODEC_ROOT_INVALID',
    });
  }
  const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
  if (pkg.name !== 'babelcodec') {
    throw Object.assign(
      new Error(`expected package name "babelcodec", got ${JSON.stringify(pkg.name)}`),
      { code: 'BABELCODEC_PACKAGE_MISMATCH' },
    );
  }
  const ver = parseVersion(pkg.version);
  if (!ver || !versionGte(ver, MIN_VERSION)) {
    throw Object.assign(
      new Error(`BabelCodec ${pkg.version} incompatible; require >= ${MIN_VERSION.join('.')}`),
      { code: 'BABELCODEC_VERSION' },
    );
  }
  const neuralPath = path.join(root, 'src', 'neural', 'index.js');
  const neural = await import(pathToFileURL(neuralPath).href);
  const required = [
    'canonicalize', 'canonicalizeBytes', 'decodeCanonical', 'serializationVersion',
    'contentHash', 'validateFeature', 'validateFeatureVector', 'validateEvent',
  ];
  const missing = required.filter((k) => typeof neural[k] !== 'function');
  if (missing.length) {
    throw Object.assign(
      new Error(`babelcodec/neural missing exports: ${missing.join(', ')}`),
      { code: 'BABELCODEC_EXPORTS' },
    );
  }
  return { neural, version: pkg.version, root };
}

async function handle(req, ctx) {
  const { neural, version, root } = ctx;
  const op = req.op;
  const payload = req.payload ?? {};
  switch (op) {
    case 'health':
      return {
        contract: CONTRACT,
        babelcodec_version: version,
        babelcodec_root: root,
        serialization: neural.serializationVersion(),
        ops: [...ALLOWED],
        node: process.version,
      };
    case 'validate_feature_vector':
      return neural.validateFeatureVector(payload.features);
    case 'canonicalize': {
      const value = payload.value;
      const text = neural.canonicalize(value);
      const bytes = neural.canonicalizeBytes(value);
      return {
        serialization: neural.serializationVersion(),
        text,
        bytes_base64: Buffer.from(bytes).toString('base64'),
        byte_length: bytes.length,
      };
    }
    case 'content_hash': {
      const domain = payload.domain;
      if (typeof domain !== 'string' || !domain) {
        throw Object.assign(new Error('content_hash requires string domain'), { code: 'BAD_PAYLOAD' });
      }
      return neural.contentHash(domain, payload.value);
    }
    case 'validate_event':
      return neural.validateEvent(payload.event);
    default:
      throw Object.assign(new Error(`op not allowed: ${op}`), { code: 'OP_DENIED' });
  }
}

async function main() {
  const root = process.env.BABELCODEC_ROOT;
  if (!root) fail(null, 'BABELCODEC_ROOT_MISSING', 'BABELCODEC_ROOT is not set');
  let raw = '';
  for await (const chunk of process.stdin) {
    raw += chunk;
    if (raw.length > 2 * 1024 * 1024) fail(null, 'REQUEST_TOO_LARGE', 'request exceeds 2 MiB');
  }
  raw = raw.trim();
  if (!raw) fail(null, 'EMPTY_REQUEST', 'empty stdin');
  let req;
  try { req = JSON.parse(raw); }
  catch (e) { fail(null, 'BAD_JSON', `invalid JSON: ${e.message}`); }
  if (!req || typeof req !== 'object') fail(null, 'BAD_REQUEST', 'request must be object');
  if (req.contract !== CONTRACT) fail(req.id, 'BAD_CONTRACT', `expected contract ${CONTRACT}`);
  if (typeof req.op !== 'string' || !ALLOWED.has(req.op)) fail(req.id, 'OP_DENIED', `op not in allowlist: ${req.op}`);
  let ctx;
  try { ctx = await loadNeural(path.resolve(root)); }
  catch (e) { fail(req.id, e.code || 'LOAD_ERROR', e.message); }
  try {
    const result = await handle(req, ctx);
    ok(req.id, result);
  } catch (e) {
    fail(req.id, e.code || 'OP_ERROR', e.message || String(e));
  }
}

main().catch((e) => fail(null, 'WORKER_CRASH', e.message || String(e)));

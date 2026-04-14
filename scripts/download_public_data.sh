#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
DATA_DIR="${ROOT_DIR}/data"

mkdir -p "${DATA_DIR}"
mkdir -p "${DATA_DIR}/desi_dr2"
mkdir -p "${DATA_DIR}/pantheonplus"
mkdir -p "${DATA_DIR}/desy5"
mkdir -p "${DATA_DIR}/cmb_compressed"

echo "==> Downloading DESI DR2 BAO public data via CobayaSampler/bao_data"
if [ ! -d "${DATA_DIR}/desi_dr2/bao_data/.git" ]; then
  git clone --filter=blob:none --no-checkout https://github.com/CobayaSampler/bao_data.git "${DATA_DIR}/desi_dr2/bao_data"
  git -C "${DATA_DIR}/desi_dr2/bao_data" sparse-checkout init --cone
  git -C "${DATA_DIR}/desi_dr2/bao_data" sparse-checkout set desi_bao_dr2 README.md
  git -C "${DATA_DIR}/desi_dr2/bao_data" checkout master || git -C "${DATA_DIR}/desi_dr2/bao_data" checkout main
else
  git -C "${DATA_DIR}/desi_dr2/bao_data" pull
fi

echo "==> Downloading Pantheon+ data release subset"
if [ ! -d "${DATA_DIR}/pantheonplus/DataRelease/.git" ]; then
  git clone --filter=blob:none --no-checkout https://github.com/PantheonPlusSH0ES/DataRelease.git "${DATA_DIR}/pantheonplus/DataRelease"
  git -C "${DATA_DIR}/pantheonplus/DataRelease" sparse-checkout init --cone
  git -C "${DATA_DIR}/pantheonplus/DataRelease" sparse-checkout set "Pantheon+_Data/4_DISTANCES_AND_COVAR"
  git -C "${DATA_DIR}/pantheonplus/DataRelease" checkout main
else
  git -C "${DATA_DIR}/pantheonplus/DataRelease" pull
fi

echo "==> Downloading DES-SN5YR / DES-Dovekie SN distance products"
if [ ! -d "${DATA_DIR}/desy5/DES-SN5YR/.git" ]; then
  git clone --filter=blob:none --no-checkout https://github.com/des-science/DES-SN5YR.git "${DATA_DIR}/desy5/DES-SN5YR"
  git -C "${DATA_DIR}/desy5/DES-SN5YR" sparse-checkout init --cone
  git -C "${DATA_DIR}/desy5/DES-SN5YR" sparse-checkout set "4_DISTANCES_COVMAT"
  git -C "${DATA_DIR}/desy5/DES-SN5YR" checkout main
else
  git -C "${DATA_DIR}/desy5/DES-SN5YR" pull
fi

echo "==> Creating convenience symlinks"
mkdir -p "${DATA_DIR}/pantheonplus/4_DISTANCES_AND_COVAR"
mkdir -p "${DATA_DIR}/desy5/4_DISTANCES_COVMAT"

ln -sfn "${DATA_DIR}/pantheonplus/DataRelease/Pantheon+_Data/4_DISTANCES_AND_COVAR" \
         "${DATA_DIR}/pantheonplus/current"

ln -sfn "${DATA_DIR}/desy5/DES-SN5YR/4_DISTANCES_COVMAT" \
         "${DATA_DIR}/desy5/current"

echo "==> Data download complete"
echo
echo "DESI DR2 BAO folder:   ${DATA_DIR}/desi_dr2/bao_data/desi_bao_dr2"
echo "Pantheon+ folder:      ${DATA_DIR}/pantheonplus/current"
echo "DES-SN5YR folder:      ${DATA_DIR}/desy5/current"
echo
echo "Reminder: place your compressed-CMB files under:"
echo "  ${DATA_DIR}/cmb_compressed/"
echo
echo "Typical DESY5 files expected by the likelihood:"
echo "  DES-Dovekie_HD.csv"
echo "  STAT+SYS.npz"
echo "  STATONLY.npz"
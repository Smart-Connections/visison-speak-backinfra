#!/bin/bash

# レイヤー用のパッケージを作成するシェルスクリプト

# コンテナを起動
CONTAINER_ID=$(docker run -v ./python/lib/python3.11/site-packages/:/layer/ -d python:3.11-slim /bin/bash -c "while true; do sleep 10; done")

# ライブラリをインストール
docker exec -it $CONTAINER_ID pip install -r /layer/requirements.txt --target /layer/

# コンテナのクリーンアップ
docker rm -f $CONTAINER_ID

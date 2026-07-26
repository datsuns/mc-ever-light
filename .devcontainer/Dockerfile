FROM eclipse-temurin:25-jdk

# 非対話モードでのパッケージインストール設定
ENV DEBIAN_FRONTEND=noninteractive

# パッケージ更新と、Minecraft/Loomの実行に必要なOpenGL・GUIライブラリ、Python3等のインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    git \
    libgl1-mesa-dri \
    libgl1 \
    libglx0 \
    libxxf86vm1 \
    libxtst6 \
    libxrandr2 \
    libxcursor1 \
    libxi6 \
    libasound2t64 \
    pulseaudio \
    sudo \
    && rm -rf /var/lib/apt/lists/*


# 開発用非rootユーザー（vscode）の作成 (ファイルの所有権トラブル防止用)
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN if getent passwd ubuntu; then userdel -f ubuntu; fi \
    && if getent group ubuntu; then groupdel ubuntu; fi \
    && groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME


# 作業スペースに適切な権限を付与するためのデフォルト環境変数
ENV DISPLAY=:0

USER $USERNAME

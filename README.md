## 🤖 ロボティクス体験キット / Robotics Experience Kit

-----

### 🚀 動作環境 (Platform & OS)

| 項目 | 詳細 |
| :--- | :--- |
| **プラットフォーム** | Raspberry Pi 4/4GB |
| **OS** | Bookworm (64bit) Normalインストールにて実証済み |
| **使用実績** | 2025年11月14日 ロボティクス体験講座にて使用 |

-----

### 🛠️ セットアップ手順 (Setup Instructions)

以下の手順に従って、リポジトリの展開とシステム設定を行ってください。

#### 1\. リポジトリのクローン

`/home/<ユーザー名>`上に **Release** リポジトリをクローンします。

```bash
$ cd
$ git clone https://github.com/yufuro/Release.git
```

#### 2\. システムファイルの初期設定

Raspberry Piのシステムファイルを初期設定します。

```bash
$ sh ./Release/setup/setup_raspi.sh
```

#### 3\. インストールと自動再起動

上記のコマンド実行後、システムが自動で再起動します。再起動後に以下のインストール作業を実行してください。

```bash
$ sh ./Release/setup/setup.sh
```

-----


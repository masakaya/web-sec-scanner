"""ZAP authentication hook script template.

This template is populated with authentication configuration values
and written to the scanner config directory at runtime.
"""
# ruff: noqa: F821, S105, E501
# type: ignore


def zap_tuned(zap):
    """ZAPチューニング後に認証を設定する。.

    Args:
        zap: ZAPv2 APIインスタンス

    """
    print("Setting up authentication via ZAP API...")

    # コンテキストを作成
    context_name = "scan-context"
    context_id = zap.context.new_context(context_name)
    print("Created context: {context_name} (ID: {context_id})")

    # コンテキストにターゲットURLを追加
    zap.context.include_in_context(context_name, "{base_url_pattern}")
    print(f"Added URL pattern to context: {base_url_pattern}")

    # Form-based認証を設定
    auth_method = "formBasedAuthentication"
    auth_params = (
        f"loginUrl={login_url}&"
        f"loginRequestData={login_data_encoded}"
    )

    zap.authentication.set_authentication_method(
        contextid=context_id,
        authmethodname=auth_method,
        authmethodconfigparams=auth_params
    )
    print("Set authentication method: {auth_method}")

    # ログイン判定の設定
    if "{logged_in_indicator}":
        zap.authentication.set_logged_in_indicator(
            contextid=context_id,
            loggedinindicatorregex="{logged_in_indicator_regex}"
        )
        print(f"Set logged-in indicator: {logged_in_indicator}")

    if "{logged_out_indicator}":
        zap.authentication.set_logged_out_indicator(
            contextid=context_id,
            loggedoutindicatorregex="{logged_out_indicator_regex}"
        )
        print(f"Set logged-out indicator: {logged_out_indicator}")

    # ユーザーを作成
    user_name = "{username}"
    user_id = zap.users.new_user(context_id, user_name)
    print("Created user: {user_name} (ID: {user_id})")

    # ユーザーの認証情報を設定
    credentials = f"{username_field}={username}&{password_field}={password}"
    zap.users.set_authentication_credentials(
        contextid=context_id,
        userid=user_id,
        authcredentialsconfigparams=credentials
    )
    print("Set authentication credentials for user: {user_name}")

    # ユーザーを有効化
    zap.users.set_user_enabled(context_id, user_id, True)
    print("Enabled user: {user_name}")

    # 強制ユーザーモードを有効化（このユーザーでスキャン）
    zap.forcedUser.set_forced_user(context_id, user_id)
    zap.forcedUser.set_forced_user_mode_enabled(True)
    print("Enabled forced user mode for: {user_name}")

    # スパイダーとアクティブスキャンでこのコンテキストを使用するように設定
    zap.context.set_context_in_scope(context_name, True)
    print("Set context in scope: {context_name}")

    print("Authentication setup completed successfully!")


def zap_spider(zap, target):
    """スパイダーをユーザーとして実行する。.

    Args:
        zap: ZAPv2 APIインスタンス
        target: ターゲットURL

    """
    print("Overriding spider to use authenticated user...")

    # コンテキストとユーザーIDを取得
    context_id = "1"
    user_id = "0"

    # 認証済みユーザーとしてスパイダーを実行
    scan_id = zap.spider.scan_as_user(context_id, user_id, target, recurse=True)
    print(f"Started spider as user (scan ID: {{scan_id}})")

    # スパイダーの完了を待つ
    import time
    while int(zap.spider.status(scan_id)) < 100:
        print(f"Spider progress: {{zap.spider.status(scan_id)}}%")
        time.sleep(5)

    print("Spider completed as authenticated user")


def zap_tuned_bearer(zap):
    """Bearer トークン認証を設定する。.

    Args:
        zap: ZAPv2 APIインスタンス

    """
    print("Setting up Bearer token authentication via ZAP API...")

    # コンテキストを作成
    context_name = "scan-context"
    zap.context.new_context(context_name)
    print("Created context: {context_name} (ID: {context_id})")

    # コンテキストにターゲットURLを追加
    zap.context.include_in_context(context_name, "{base_url_pattern}")
    print(f"Added URL pattern to context: {base_url_pattern}")

    # トークン値を準備（プレフィックスの処理）
    token_prefix = "{token_prefix}"
    auth_token = "{auth_token}"
    auth_header = "{auth_header}"

    if token_prefix and token_prefix.lower() != "none":
        token_value = "{token_prefix} {auth_token}"
    else:
        token_value = auth_token

    print(f"Token header: {{auth_header}}")
    print(f"Token value: {{token_value[:20]}}..." if len(token_value) > 20 else f"Token value: {{token_value}}")

    # ZAP Replacer APIを使用してAuthorizationヘッダーを追加
    # すべてのリクエストにトークンヘッダーを追加
    try:
        zap.replacer.add_rule(
            description="Add Bearer Token Header",
            enabled=True,
            matchtype="REQ_HEADER",
            matchstring=auth_header,
            matchregex=False,
            replacement=token_value
        )
        print("Added replacer rule for {auth_header} header")
    except Exception:
        print("Warning: Could not add replacer rule: {e}")
        print("Token authentication may not work correctly")

    # コンテキストをスコープ内に設定
    zap.context.set_context_in_scope(context_name, True)
    print("Set context in scope: {context_name}")

    print("Bearer token authentication setup completed successfully!")


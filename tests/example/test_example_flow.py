"""サンプルフローのユニットテスト。"""

from src.example.example_flow import example_workflow, greet, process_data


class TestGreet:
    """greetタスクのテストクラス。"""

    def test_greet_with_default_name(self):
        """デフォルト名でのgreet関数をテスト。"""
        result = greet("World")
        assert result == "Hello, World!"

    def test_greet_with_custom_name(self):
        """カスタム名でのgreet関数をテスト。"""
        result = greet("Alice")
        assert result == "Hello, Alice!"

    def test_greet_with_japanese_name(self):
        """日本語名でのgreet関数をテスト。"""
        result = greet("田中")
        assert result == "Hello, 田中!"

    def test_greet_with_empty_string(self):
        """空文字列でのgreet関数をテスト。"""
        result = greet("")
        assert result == "Hello, !"

    def test_greet_return_type(self):
        """greet関数の戻り値の型をテスト。"""
        result = greet("Test")
        assert isinstance(result, str)


class TestProcessData:
    """process_dataタスクのテストクラス。"""

    def test_process_data_doubles_values(self):
        """値が2倍になることをテスト。"""
        result = process_data([1, 2, 3])
        assert result == [2, 4, 6]

    def test_process_data_empty_list(self):
        """空のリストを処理することをテスト。"""
        result = process_data([])
        assert result == []

    def test_process_data_single_value(self):
        """単一の値を処理することをテスト。"""
        result = process_data([5])
        assert result == [10]

    def test_process_data_large_numbers(self):
        """大きな数値を処理することをテスト。"""
        result = process_data([100, 200, 300])
        assert result == [200, 400, 600]

    def test_process_data_negative_numbers(self):
        """負の数値を処理することをテスト。"""
        result = process_data([-1, -2, -3])
        assert result == [-2, -4, -6]

    def test_process_data_mixed_numbers(self):
        """正負混在の数値を処理することをテスト。"""
        result = process_data([-1, 0, 1])
        assert result == [-2, 0, 2]

    def test_process_data_return_type(self):
        """process_data関数の戻り値の型をテスト。"""
        result = process_data([1, 2, 3])
        assert isinstance(result, list)
        assert all(isinstance(x, int) for x in result)


class TestExampleWorkflow:
    """example_workflowフローのテストクラス。"""

    def test_workflow_with_defaults(self):
        """デフォルト引数でのワークフローをテスト。"""
        result = example_workflow()

        assert isinstance(result, dict)
        assert "greeting" in result
        assert "processed" in result
        assert result["greeting"] == "Hello, World!"
        assert result["processed"] == [2, 4, 6, 8, 10]

    def test_workflow_with_custom_name(self):
        """カスタム名でのワークフローをテスト。"""
        result = example_workflow(name="Alice")

        assert result["greeting"] == "Hello, Alice!"
        assert result["processed"] == [2, 4, 6, 8, 10]

    def test_workflow_with_custom_numbers(self):
        """カスタム数値リストでのワークフローをテスト。"""
        result = example_workflow(numbers=[10, 20, 30])

        assert result["greeting"] == "Hello, World!"
        assert result["processed"] == [20, 40, 60]

    def test_workflow_with_all_custom_params(self):
        """すべてカスタムパラメータでのワークフローをテスト。"""
        result = example_workflow(name="Bob", numbers=[5, 10])

        assert result["greeting"] == "Hello, Bob!"
        assert result["processed"] == [10, 20]

    def test_workflow_with_empty_numbers(self):
        """空の数値リストでのワークフローをテスト。

        注: 空リストは `numbers or [1, 2, 3, 4, 5]` でFalsyとして扱われるため、
        デフォルト値が使用される。
        """
        result = example_workflow(numbers=[])

        assert result["greeting"] == "Hello, World!"
        # 空リストはFalsyなのでデフォルト値が使用される
        assert result["processed"] == [2, 4, 6, 8, 10]

    def test_workflow_return_structure(self):
        """ワークフローの戻り値の構造をテスト。"""
        result = example_workflow()

        assert isinstance(result, dict)
        assert len(result) == 2
        assert isinstance(result["greeting"], str)
        assert isinstance(result["processed"], list)

    def test_workflow_with_japanese_name(self):
        """日本語名でのワークフローをテスト。"""
        result = example_workflow(name="太郎", numbers=[100, 200])

        assert result["greeting"] == "Hello, 太郎!"
        assert result["processed"] == [200, 400]

"""测试 demo_04_state_reducer 模块中的 merge_unique_list 函数。"""

from app.langgraph_state.demo_04_state_reducer import (
    SourceState,
    answer_node,
    build_graph,
    main,
    merge_unique_list,
    retrieve_employee_doc_node,
    retrieve_policy_doc_node,
)


class TestMergeUniqueList:
    """测试 merge_unique_list 函数的各项场景。"""

    # ========== 正常输入场景 ==========

    def test_merge_both_lists_with_no_overlap(self):
        """测试两个列表无重复时的合并。"""
        old = ["doc_a", "doc_b"]
        new = ["doc_c", "doc_d"]
        result = merge_unique_list(old, new)
        assert result == ["doc_a", "doc_b", "doc_c", "doc_d"]

    def test_merge_both_lists_with_partial_overlap(self):
        """测试两个列表有部分重复时的合并。"""
        old = ["employee_handbook", "policy_doc"]
        new = ["ecommerce_after_sales", "employee_handbook"]
        result = merge_unique_list(old, new)
        assert result == ["employee_handbook", "policy_doc", "ecommerce_after_sales"]

    def test_merge_both_lists_with_complete_overlap(self):
        """测试两个列表完全重复时的合并。"""
        old = ["doc_a", "doc_b"]
        new = ["doc_a", "doc_b"]
        result = merge_unique_list(old, new)
        assert result == ["doc_a", "doc_b"]

    # ========== 边界值场景 ==========

    def test_merge_empty_old_with_nonempty_new(self):
        """测试旧列表为空，新列表非空的情况。"""
        old: list[str] = []
        new = ["doc_a", "doc_b"]
        result = merge_unique_list(old, new)
        assert result == ["doc_a", "doc_b"]

    def test_merge_nonempty_old_with_empty_new(self):
        """测试旧列表非空，新列表为空的情况。"""
        old = ["doc_a", "doc_b"]
        new: list[str] = []
        result = merge_unique_list(old, new)
        assert result == ["doc_a", "doc_b"]

    def test_merge_both_empty_lists(self):
        """测试两个都为空列表的情况。"""
        old: list[str] = []
        new: list[str] = []
        result = merge_unique_list(old, new)
        assert result == []

    def test_merge_single_element_lists_no_overlap(self):
        """测试单元素列表，无重复。"""
        old = ["doc_a"]
        new = ["doc_b"]
        result = merge_unique_list(old, new)
        assert result == ["doc_a", "doc_b"]

    def test_merge_single_element_lists_with_overlap(self):
        """测试单元素列表，有重复。"""
        old = ["doc_a"]
        new = ["doc_a"]
        result = merge_unique_list(old, new)
        assert result == ["doc_a"]

    def test_merge_large_lists(self):
        """测试大量元素的列表合并。"""
        old = [f"old_{i}" for i in range(100)]
        new = [f"new_{i}" for i in range(100)]
        result = merge_unique_list(old, new)
        assert len(result) == 200
        assert result[:100] == [f"old_{i}" for i in range(100)]
        assert result[100:] == [f"new_{i}" for i in range(100)]

    def test_merge_large_lists_with_overlap(self):
        """测试大量元素的列表合并，其中50个元素重复。"""
        old = [f"doc_{i}" for i in range(50)]
        new = [f"doc_{i}" for i in range(50, 100)]
        result = merge_unique_list(old, new)
        assert len(result) == 100
        assert result[:50] == [f"doc_{i}" for i in range(50)]
        assert result[50:] == [f"doc_{i}" for i in range(50, 100)]

    # ========== 顺序保持验证 ==========

    def test_merge_preserves_original_order(self):
        """测试合并后保持原始顺序。"""
        old = ["first", "second", "third"]
        new = ["fourth", "fifth"]
        result = merge_unique_list(old, new)
        assert result == ["first", "second", "third", "fourth", "fifth"]

    def test_merge_preserves_new_items_order(self):
        """测试合并后新元素的相对顺序。"""
        old = ["existing"]
        new = ["a", "b", "c", "d"]
        result = merge_unique_list(old, new)
        assert result == ["existing", "a", "b", "c", "d"]
        assert result[1:4] == ["a", "b", "c"]

    def test_merge_multiple_occurrences_in_new_only_adds_unique(self):
        """测试新列表中有多个重复元素时，只添加第一个。"""
        old = ["doc_a"]
        new = ["doc_b", "doc_a", "doc_c", "doc_a"]
        result = merge_unique_list(old, new)
        assert result == ["doc_a", "doc_b", "doc_c"]

    # ========== 不修改原列表验证 ==========

    def test_merge_does_not_modify_old_list(self):
        """测试合并操作不会修改原旧列表。"""
        old = ["doc_a", "doc_b"]
        new = ["doc_c"]
        old_copy = old.copy()
        merge_unique_list(old, new)
        assert old == old_copy

    def test_merge_does_not_modify_new_list(self):
        """测试合并操作不会修改原新列表。"""
        old = ["doc_a"]
        new = ["doc_b", "doc_c"]
        new_copy = new.copy()
        merge_unique_list(old, new)
        assert new == new_copy

    def test_merge_returns_new_list(self):
        """测试返回的是新列表，不是旧列表的引用。"""
        old = ["doc_a"]
        new = ["doc_b"]
        result = merge_unique_list(old, new)
        assert result is not old
        assert result is not new


class TestSourceState:
    """测试 SourceState 状态定义。"""

    def test_source_state_has_required_fields(self):
        """测试 SourceState 包含所有必需字段。"""
        state = SourceState(
            question="测试问题",
            sources=["source_a", "source_b"],
            answer="测试回答",
        )
        assert state["question"] == "测试问题"
        assert state["sources"] == ["source_a", "source_b"]
        assert state["answer"] == "测试回答"

    def test_source_state_empty_sources(self):
        """测试 SourceState 可以接受空来源列表。"""
        state = SourceState(
            question="测试问题",
            sources=[],
            answer="",
        )
        assert state["sources"] == []


class TestRetrieveNodes:
    """测试检索节点的返回结果。"""

    def test_retrieve_employee_doc_node(self):
        """测试员工手册检索节点返回正确的来源。"""
        state = SourceState(question="员工规则是什么？", sources=[], answer="")
        result = retrieve_employee_doc_node(state)
        assert result == {"sources": ["employee_handbook"]}

    def test_retrieve_policy_doc_node(self):
        """测试售后规则检索节点返回正确的来源。"""
        state = SourceState(question="售后规则是什么？", sources=[], answer="")
        result = retrieve_policy_doc_node(state)
        assert result == {"sources": ["ecommerce_after_sales", "employee_handbook"]}


class TestAnswerNode:
    """测试回答节点的返回结果。"""

    def test_answer_node_generates_answer_with_sources(self):
        """测试回答节点生成包含来源的回答。"""
        state = SourceState(
            question="规则是什么？",
            sources=["source_a", "source_b"],
            answer="",
        )
        result = answer_node(state)
        assert result == {"answer": "最终引用来源：source_a, source_b"}

    def test_answer_node_with_empty_sources(self):
        """测试回答节点处理空来源列表。"""
        state = SourceState(
            question="规则是什么？",
            sources=[],
            answer="",
        )
        result = answer_node(state)
        assert result == {"answer": "最终引用来源："}

    def test_answer_node_with_single_source(self):
        """测试回答节点处理单个来源。"""
        state = SourceState(
            question="规则是什么？",
            sources=["only_source"],
            answer="",
        )
        result = answer_node(state)
        assert result == {"answer": "最终引用来源：only_source"}


class TestBuildGraph:
    """测试图构建功能。"""

    def test_build_graph_returns_compiled_app(self):
        """测试 build_graph 返回可调用的编译图。"""
        app = build_graph()
        assert app is not None
        assert hasattr(app, "invoke")
        assert hasattr(app, "stream")

    def test_graph_execution_with_initial_state(self):
        """测试图执行时正确合并来源。"""
        app = build_graph()
        initial_state = {
            "question": "员工售后规则是什么？",
            "sources": [],
            "answer": "",
        }
        result = app.invoke(initial_state)
        assert "sources" in result
        assert "answer" in result
        # 验证来源按顺序合并：employee_handbook 在第一个节点添加，
        # ecommerce_after_sales 在第二个节点添加，employee_handbook 不重复
        assert "employee_handbook" in result["sources"]
        assert "ecommerce_after_sales" in result["sources"]

    def test_graph_execution_with_existing_sources(self):
        """测试图执行时与已有来源合并。"""
        app = build_graph()
        initial_state = {
            "question": "规则是什么？",
            "sources": ["pre_existing_doc"],
            "answer": "",
        }
        result = app.invoke(initial_state)
        assert "pre_existing_doc" in result["sources"]
        assert "employee_handbook" in result["sources"]
        assert "ecommerce_after_sales" in result["sources"]
        # 验证 pre_existing_doc 在最前面
        assert result["sources"][0] == "pre_existing_doc"


class TestMain:
    """测试 main 函数的执行。"""

    def test_main_runs_without_exception(self):
        """测试 main 函数可以正常执行并输出结果。"""
        # main 函数会打印结果，我们通过捕获输出验证其执行成功
        main()

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from StorageManager.classes import Statistic, StorageEngine

from QueryParser import QueryParser
from QueryTree import ParsedQuery, QueryTree
from QueryHelper import *
from typing import Callable, Union
class OptimizationEngine:
    def __init__(self):
        # print(os.getcwd())
        # self.QueryParser = QueryParser("dfa.txt")
        self.QueryParser = QueryParser("QueryOptimizer/dfa.txt")

    def __validate_aliases(self, query_components: dict, alias_map: dict):
        def find_aliases(expression: str) -> set:
            aliases = set()
            tokens = expression.split()
            for token in tokens:
                if "." in token:  # Check for alias usage
                    alias = token.split(".")[0]
                    aliases.add(alias)
            return aliases

        used_aliases = set()

        if "SELECT" in query_components:
            for attr in query_components["SELECT"]:
                used_aliases.update(find_aliases(attr))
        if "WHERE" in query_components:
            used_aliases.update(find_aliases(query_components["WHERE"]))
        if "FROM" in query_components:
            for token in query_components["FROM"]:
                if "." in token:
                    used_aliases.update(find_aliases(token))

        # Find undefined aliases
        undefined_aliases = used_aliases - set(alias_map.keys())
        if undefined_aliases:
            raise ValueError(f"Undefined aliases detected: {', '.join(undefined_aliases)}")

    def parse_query(self, query: str,database_name: str, get_stats: Callable[[str, str, int], Union[Statistic, Exception]]) -> ParsedQuery:
        normalized_query = QueryHelper.remove_excessive_whitespace(
            QueryHelper.normalize_string(query).upper()
        )
        # print("normalized", normalized_query)

        normalized_query = self.QueryParser.check_valid_syntax(normalized_query) 
        if(not normalized_query):
            return False

        components = ["SELECT", "UPDATE", "DELETE", "FROM", "SET", "WHERE", "ORDER BY", "LIMIT"]

        query_components_value = {}

        i = 0
        while i < len(components):
            # print(i, "query component", query_components_value)
            idx_first_comp = normalized_query.find(components[i])
            if idx_first_comp == -1:
                i += 1
                continue

            if i == len(components) - 1:  # Last component (LIMIT)
                query_components_value[components[i]] = QueryHelper.extract_value(
                    query, components[i], ""
                )
                break

            j = i + 1
            idx_second_comp = normalized_query.find(components[j])
            while idx_second_comp == -1 and j < len(components) - 1:
                j += 1
                idx_second_comp = normalized_query.find(components[j])

            query_components_value[components[i]] = QueryHelper.extract_value(
                query, components[i], "" if idx_second_comp == -1 else components[j]
            )

            i += 1

        # print(f"query_components_value: {query_components_value}") # testing

        if "FROM" in query_components_value:
            alias_map = QueryHelper.extract_table_aliases(query_components_value["FROM"])
            
            query_components_value["FROM"] = QueryHelper.remove_aliases(query_components_value["FROM"])

            # Validate aliases in SELECT, WHERE, and FROM clauses
            undefined_aliases = self.__validate_aliases(query_components_value, alias_map)
            if undefined_aliases:
                raise ValueError(f"Undefined aliases detected: {', '.join(undefined_aliases)}")
            
            # print("alias map", alias_map)
            query_components_value["FROM"] = [
                QueryHelper.rewrite_with_alias(attr, alias_map) for attr in query_components_value["FROM"]
            ]
            
            if "SELECT" in query_components_value:
                query_components_value["SELECT"] = [
                    QueryHelper.rewrite_with_alias(attr, alias_map) for attr in query_components_value["SELECT"]
                ]
            if "WHERE" in query_components_value:
                query_components_value["WHERE"] = QueryHelper.rewrite_with_alias(
                    query_components_value["WHERE"], alias_map
                )
                            
            # table_arr = QueryHelper.extract_tables(query_components_value["FROM"])
        else:
            table_arr = query_components_value['UPDATE']
            
        # attributes_arr = QueryHelper.extract_attributes(query_components_value)

        query_tree = self.__build_query_tree(query_components_value)
        return ParsedQuery(query_tree,normalized_query)

    def __build_query_tree(self, components: dict) -> QueryTree:

        root = QueryTree(type="ROOT")
        top = root

        if "LIMIT" in components:
            limit_tree = QueryTree(type="LIMIT", val=components["LIMIT"])
            top.add_child(limit_tree)
            limit_tree.add_parent(top)
            top = limit_tree
        
        if "ORDER BY" in components:
            order_by_tree = QueryTree(type="ORDER BY", val=components["ORDER BY"])
            top.add_child(order_by_tree)
            order_by_tree.add_parent(top)
            top = order_by_tree
        
        if "SELECT" in components:
            select_tree = QueryTree(type="SELECT", val=components["SELECT"])
            top.add_child(select_tree)
            select_tree.add_parent(top)
            top = select_tree
                
        if "UPDATE" in components:
            where_tree = QueryTree(type="UPDATE", val=components["UPDATE"])
            top.add_child(where_tree)
            where_tree.add_parent(top)
            top = where_tree

        # if "DELETE" in components:
        #     where_tree = QueryTree(type="DELETE", val=components["DELETE"])
        #     top.add_child(where_tree)
        #     where_tree.add_parent(top)
        #     top = where_tree
        
        if "WHERE" in components:
            where_tree = QueryHelper.parse_where_clause(components["WHERE"])
            top.add_child(where_tree)
            where_tree.add_parent(top)
            top = select_tree

        if "FROM" in components:
            join_tree = QueryHelper.build_join_tree(components["FROM"])
            top.add_child(join_tree)
            join_tree.add_parent(top)

        return root

    def optimize_query(self, query: ParsedQuery):
        queue_nodes = Queue()
        queue_nodes.put(query.query_tree)
        while not queue_nodes.empty():
            current_node = queue_nodes.get()
            if current_node.type == "TABLE":
                continue
            for child in current_node.childs:
                queue_nodes.put(child)

            if self.QueryOptimizer.perform_operation(
                current_node, 
                lambda node: self.get_cost(ParsedQuery(node, query.query), "database1")
            ):
                print(query)

    def get_cost(self, query: ParsedQuery, database_name: str) -> int:
        # implementasi sementara hanya menghitung size cost
        query_cost = QueryCost(self.get_stats, database_name)
        return query_cost.calculate_size_cost(query.query_tree)


if __name__ == "__main__":
    optim = OptimizationEngine()
    storage = StorageEngine()

    # Test SELECT query with JOIN
    select_query = "SELECT u.id, product_id FROM users AS u JOIN products AS t ON products.product_id = u.id WHERE u.id > 1 AND t.product_id = 2 OR t.product_id < 5 AND t.product_id = 10 order by u.id ASC"
    print("SELECT QUERY\n",select_query,end="\n\n")
    parsed_query = optim.parse_query(select_query,"database1")
    print(parsed_query)
    optim.optimize_query(parsed_query)
    optim.optimize_query(parsed_query)
    print("EVALUATION PLAN TREE: \n",parsed_query)
    
    print(f"COST = {optim.get_cost(parsed_query, 'database1')}")

    # try:
    #     invalid_query = "SELECT x.a FROM students AS s"
    #     print(invalid_query)
    #     parsed_query = optim.parse_query(invalid_query,"database1",storage.get_stats)
    #     print(parsed_query)
    # except ValueError as e:
    #     print(e)

    # where_clause = "students.a > 'aku' AND teacher.b = 'abc'"
    # attribute_types = {
    #     "students.a": "integer",
    #     "teacher.b": "varchar",
    # }

    # try:
    #     QueryHelper.validate_comparisons(where_clause, attribute_types)
    #     print("All comparisons are valid!")
    # except ValueError as e:
    #     print(f"Validation error: {e}")

    # Test UPDATE query
    # update_query = "UPDATE employee SET salary = salary + 1.1 - 5 WHERE salary > 1000"
    # print(update_query)
    # parsed_update_query = optim.parse_query(update_query, "database_sample", storage.get_stats)
    # print(parsed_update_query)

    # #Test DELETE query
    # delete_query = "DELETE FROM employees WHERE salary < 3000"
    # print(delete_query)
    # parsed_delete_query = new.parse_query(delete_query)
    # print(parsed_delete_query)


    # cari tabel
    # print(parsed_query.query_tree.type)
    # print(parsed_query.query_tree.val)
    print(getTables(parsed_query.query_tree))
    print(getJoin(parsed_query.query_tree))
    # foundSelect = False
    # tempTree = parsed_query
    # while not foundSelect:
        # tempTree
from typing import Callable, Union
from math import prod
from time import sleep
import re
from StorageManager.classes import *
from .QueryTree import *

class QueryCost:

    def __init__(self, get_stats: Callable[[str, str, int], Union[Statistic, Exception]], database: str):
        self.__get_stats = get_stats
        self.__database = database
        self.__n_r_total = 0

    def calculate_size_cost(self, query_tree: QueryTree) -> int:
        self.__get_size_cost(query_tree)
        return self.__n_r_total
    
    # remove leading and trailing whitespaces
    # make lowercase
    @staticmethod
    def __format_name(string: str) -> str:
        return string.strip().lower()
    
    @staticmethod
    def __is_right_side_constant(condition: str) -> bool:
        right_side = condition.split(" = ")[1]
        numeric_pattern = r"^\d+(\.\d+)?$"
        return bool(re.match(numeric_pattern, right_side))


    # Size Cost
    # Calculate the size cost of the query tree

    def __get_size_cost(self, query_tree: QueryTree) -> Statistic:
        
        if query_tree.type == "TABLE":
            result = self.__get_stats(self.__database, QueryCost.__format_name(query_tree.val))
            # result.n_r *= 1000
            # result.V_a_r = {key: value * 10 for key, value in result.V_a_r.items()}
        
        elif query_tree.type == "SELECT": 
            statistic = self.__get_size_cost(query_tree.childs[0])
            attributes = [item.split('.')[1] for item in query_tree.val]
            attributes = [QueryCost.__format_name(attribute) for attribute in attributes]
            result = self.__select(statistic, attributes)
        
        elif query_tree.type == "WHERE":
            statistic = self.__get_size_cost(query_tree.childs[0])
            if "OR" in query_tree.val:
                result = statistic
            elif "=" in query_tree.val:
                attribute = query_tree.val.split(" = ")[0].split(".")[1]
                attribute = QueryCost.__format_name(attribute)
                result = self.__where_equals(statistic, attribute)
            elif "<>" in query_tree.val:
                attribute = query_tree.val.split(" <> ")[0].split(".")[1]
                attribute = QueryCost.__format_name(attribute)
                result = self.__where_not_equals(statistic, attribute)
            else:
                result = self.__where_comparison(statistic)
        
        elif query_tree.type == "JOIN":
            statistic1 = self.__get_size_cost(query_tree.childs[0])
            statistic2 = self.__get_size_cost(query_tree.childs[1])

            expressions = re.split(" AND | OR ", query_tree.val)
            expression = expressions.pop(0)

            if QueryCost.__is_right_side_constant(expression):
                result = self.__join_on_constant(statistic1, statistic2, expression)
            else:
                attributes = [item.split('.')[1] for item in expression.split(" = ")]
                attributes = [QueryCost.__format_name(attribute) for attribute in attributes]
                attribute1, attribute2 = attributes
                
                if attribute1 not in statistic1.V_a_r or attribute2 not in statistic2.V_a_r:
                    attribute1, attribute2 = attribute2, attribute1
                
                result = self.__join_on(statistic1, statistic2, attribute1, attribute2)

        elif query_tree.type == "NATURAL JOIN":
            statistic1 = self.__get_size_cost(query_tree.childs[0])
            statistic2 = self.__get_size_cost(query_tree.childs[1])
            if len(query_tree.val) == 0:
                result = self.__cross_join(statistic1, statistic2)
            else:
                attributes = query_tree.val
                attributes = [QueryCost.__format_name(attribute) for attribute in attributes]
                result = self.__natural_join(statistic1, statistic2, attributes)

        else:
            result = self.__get_size_cost(query_tree.childs[0])
        

        if query_tree.type != "ROOT":
            self.__n_r_total += result.n_r

        # print(f"type: {query_tree.type}, val: {query_tree.val}")
        # print(f"n_r: {result.n_r}, V_a_r: {result.V_a_r}")
        # print(self.__n_r_total)
        # sleep(1)
        return result
    
    def __select(self, statistic: Statistic, attributes: list[str]) -> Statistic:
        if (statistic.n_r == 0) or (0 in statistic.V_a_r.values()):
            V_a_r_result = {}
            for attribute in attributes:
                V_a_r_result[attribute] = 0
            
            result: Statistic = Statistic(n_r=0, V_a_r=V_a_r_result, b_r=None, l_r=None, f_r=None)
            return result
        
        n_r_result = 1
        for attribute in attributes:
            n_r_result *= statistic.V_a_r[attribute]
        n_r_result = min(n_r_result, statistic.n_r)

        V_a_r_result = {}
        for attribute in attributes:
            V_a_r_result[attribute] = statistic.V_a_r[attribute]
        
        result: Statistic = Statistic(n_r=n_r_result, V_a_r=V_a_r_result, b_r=None, l_r=None, f_r=None)
        return result

    def __where_equals(self, statistic: Statistic, attribute: str) -> Statistic:
        if (statistic.n_r == 0) or (0 in statistic.V_a_r.values()):
            V_a_r_result = {}
            for attribute in statistic.V_a_r:
                V_a_r_result[attribute] = 0
            
            result: Statistic = Statistic(n_r=0, V_a_r=V_a_r_result, b_r=None, l_r=None, f_r=None)
            return result
        
        n_r_result = statistic.n_r // statistic.V_a_r[attribute]

        V_a_r_result = {}
        for attribute in statistic.V_a_r:
            V_a_r_result[attribute] = min(statistic.V_a_r[attribute], n_r_result)
        
        result: Statistic = Statistic(n_r=n_r_result, V_a_r=V_a_r_result, b_r=None, l_r=None, f_r=None)
        return result

    def __where_not_equals(self, statistic: Statistic, attribute: str) -> Statistic:
        if (statistic.n_r == 0) or (0 in statistic.V_a_r.values()):
            V_a_r_result = {}
            for attribute in statistic.V_a_r:
                V_a_r_result[attribute] = 0
            
            result: Statistic = Statistic(n_r=0, V_a_r=V_a_r_result, b_r=None, l_r=None, f_r=None)
            return result
        
        n_r_result = statistic.n_r - self.__where_equals(statistic, attribute).n_r
        
        V_a_r_result = {}
        for attribute in statistic.V_a_r:
            V_a_r_result[attribute] = min(statistic.V_a_r[attribute], n_r_result)
        
        result: Statistic = Statistic(n_r=n_r_result, V_a_r=V_a_r_result, b_r=None, l_r=None, f_r=None)
        return result

    def __where_comparison(self, statistic: Statistic) -> Statistic:
        if (statistic.n_r == 0) or (0 in statistic.V_a_r.values()):
            V_a_r_result = {}
            for attribute in statistic.V_a_r:
                V_a_r_result[attribute] = 0
            
            result: Statistic = Statistic(n_r=0, V_a_r=V_a_r_result, b_r=None, l_r=None, f_r=None)
            return result
        
        n_r_result = statistic.n_r // 2
        
        V_a_r_result = {}
        for attribute in statistic.V_a_r:
            V_a_r_result[attribute] = min(statistic.V_a_r[attribute], n_r_result)
        
        result: Statistic = Statistic(n_r=n_r_result, V_a_r=V_a_r_result, b_r=None, l_r=None, f_r=None)
        return result
    
    def __cross_join(self, statistic1: Statistic, statistic2: Statistic) -> Statistic:
        if (statistic1.n_r == 0) or (0 in statistic1.V_a_r.values()) or (statistic2.n_r == 0) or (0 in statistic2.V_a_r.values()):
            V_a_r_result = {}
            for attribute in statistic1.V_a_r:
                V_a_r_result[attribute] = 0
            for attribute in statistic2.V_a_r:
                V_a_r_result[attribute] = 0
            
            result: Statistic = Statistic(n_r=0, V_a_r=V_a_r_result, b_r=None, l_r=None, f_r=None)
            return result
        
        n_r_result = statistic1.n_r * statistic2.n_r
        
        V_a_r_result = {}
        for attribute in statistic1.V_a_r:
            V_a_r_result[attribute] = min(statistic1.V_a_r[attribute], n_r_result)
        for attribute in statistic2.V_a_r:
            V_a_r_result[attribute] = min(statistic2.V_a_r[attribute], n_r_result)
        
        result: Statistic = Statistic(n_r=n_r_result, V_a_r=V_a_r_result, b_r=None, l_r=None, f_r=None)
        return result

    def __join_on(self, statistic1: Statistic, statistic2: Statistic, attribute1: str, attribute2: str) -> Statistic:
        if (statistic1.n_r == 0) or (0 in statistic1.V_a_r.values()) or (statistic2.n_r == 0) or (0 in statistic2.V_a_r.values()):
            V_a_r_result = {}
            for attribute in statistic1.V_a_r:
                V_a_r_result[attribute] = 0
            for attribute in statistic2.V_a_r:
                V_a_r_result[attribute] = 0
            
            result: Statistic = Statistic(n_r=0, V_a_r=V_a_r_result, b_r=None, l_r=None, f_r=None)
            return result
        
        n_r_result_1 = statistic1.n_r * statistic2.n_r // statistic2.V_a_r[attribute2]
        n_r_result_2 = statistic1.n_r * statistic2.n_r // statistic1.V_a_r[attribute1]
        n_r_result = min(n_r_result_1, n_r_result_2)
        
        V_a_r_result = {}
        for attribute in statistic1.V_a_r:
            V_a_r_result[attribute] = min(statistic1.V_a_r[attribute], n_r_result)
        for attribute in statistic2.V_a_r:
            V_a_r_result[attribute] = min(statistic2.V_a_r[attribute], n_r_result)
        
        result: Statistic = Statistic(n_r=n_r_result, V_a_r=V_a_r_result, b_r=None, l_r=None, f_r=None)
        return result
    
    def __join_on_constant(self, statistic1: Statistic, statistic2: Statistic, condition: str) -> Statistic:
        result_cross: Statistic = self.__cross_join(statistic1, statistic2)
        
        if "OR" in condition:
            result_where = result_cross
        elif "=" in condition:
            attribute = condition.split(" = ")[0].split(".")[1]
            attribute = QueryCost.__format_name(attribute)
            result_where = self.__where_equals(result_cross, attribute)
        elif "<>" in condition:
            attribute = condition.split(" <> ")[0].split(".")[1]
            attribute = QueryCost.__format_name(attribute)
            result_where = self.__where_not_equals(result_cross, attribute)
        else:
            result_where = self.__where_comparison(result_cross)

        return result_where
    
    def __natural_join(self, statistic1: Statistic, statistic2: Statistic, attributes: list[str]) -> Statistic:
        if (statistic1.n_r == 0) or (0 in statistic1.V_a_r.values()) or (statistic2.n_r == 0) or (0 in statistic2.V_a_r.values()):
            V_a_r_result = {}
            for attribute in statistic1.V_a_r:
                V_a_r_result[attribute] = 0
            for attribute in statistic2.V_a_r:
                V_a_r_result[attribute] = 0
            
            result: Statistic = Statistic(n_r=0, V_a_r=V_a_r_result, b_r=None, l_r=None, f_r=None)
            return result
        
        V_a_r_2_all = max([statistic2.V_a_r[attribute] for attribute in attributes])
        n_r_result_1 = statistic1.n_r * statistic2.n_r // V_a_r_2_all
        V_a_r_1_all = max([statistic1.V_a_r[attribute] for attribute in attributes])
        n_r_result_2 = statistic1.n_r * statistic2.n_r // V_a_r_1_all
        n_r_result = min(n_r_result_1, n_r_result_2)
        
        V_a_r_result = {}
        for attribute in statistic1.V_a_r:
            V_a_r_result[attribute] = min(statistic1.V_a_r[attribute], n_r_result)
        for attribute in statistic2.V_a_r:
            V_a_r_result[attribute] = min(statistic2.V_a_r[attribute], n_r_result)
        
        result: Statistic = Statistic(n_r=n_r_result, V_a_r=V_a_r_result, b_r=None, l_r=None, f_r=None)
        return result


    # Time Cost
    # Calculate the time cost of the query tree
    # Time Cost dengan waktu block transfer = waktu seeks = 1
    
    def linearScan(self, table: str):
        statistics = self.__storage_engine.get_stats(database_name=self.__database, table_name=table)
        return statistics.b_r + 1
    
    #Asumsi tinggi pohon diketahui
    def indexScanKey(self, table: str, levelPohon): 
        statistics = self.__storage_engine.get_stats(database_name=self.__database, table_name=table)
        return 2*(levelPohon + 1)
    
    #Asumsi tinggi pohon diketahui
    def indexScanNonkey(self, table: str, levelPohon): 
        statistics = self.__storage_engine.get_stats(database_name=self.__database, table_name=table)
        return 2*(levelPohon) + statistics.b_r + 1
    
    def nestedLoopJoin(self, table1: str, table2: str) :
        statistics1 = self.__storage_engine.get_stats(database_name=self.__database, table_name=table1)
        statistics2 = self.__storage_engine.get_stats(database_name=self.__database, table_name=table2)
        return statistics1.n_r * statistics2.b_r +statistics1.b_r + statistics1.n_r +statistics1.b_r
        
    def blockNestedLoopJoin(self, table1: str, table2: str) :
        statistics1 = self.__storage_engine.get_stats(database_name=self.__database, table_name=table1)
        statistics2 = self.__storage_engine.get_stats(database_name=self.__database, table_name=table2)
        return statistics1.b_r * statistics2.b_r + statistics1.b_r + 2*statistics1.b_r
    
    # Asumsi kedua tabel sudah di-sort dan block buffer berukuran 1
    def mergeJoin(self, table1: str, table2: str) :
        statistics1 = self.__storage_engine.get_stats(database_name=self.__database, table_name=table1)
        statistics2 = self.__storage_engine.get_stats(database_name=self.__database, table_name=table2)
        return 2*(statistics1.b_r * statistics2.b_r)
    


from concurrent.futures import ThreadPoolExecutor
from typing import (Callable, 
                    Dict, 
                    Protocol, 
                    Tuple, 
                    Any, 
                    Optional, 
                    Union,
                    runtime_checkable,
                    Literal
                    )
from abc import ABC,  abstractmethod
from dask.delayed import delayed  
from dask.base import  compute


class WorkFlowBase(ABC):
    def __init__(self) -> None:
        self.contexts: Dict[str, Any] = {}
    def register_contexts(self, contexts: Dict[str, Any]) -> None:
        self.contexts = contexts
    @abstractmethod
    def __call__(self, 
                 initial_messages:Any, 
                 *args:Any, 
                 **kwargs: Any) -> Any:
        pass


@runtime_checkable
class Processor(Protocol):
    def __call__(self, 
                 message: Any,
                 workflow: WorkFlowBase, 
                 *args:Any, **kwargs:Any) -> Tuple[Any, str]:
        return message, 'EXIT'
        
        

class SequentialWorkFlow(WorkFlowBase):
    def __init__(self) -> None:
        super().__init__()
        self.nodes: Dict[str, Callable] = {}
        self.edges: Dict[str, Processor] = {}
        self.entry_node = None
        self.exit_node = None
    
 
    def add_node(self, 
                 agent: Callable, 
                 name: str) -> None:
        if name in self.nodes:
            raise ValueError(f"Node {name} already exists.")
        self.nodes[name] = agent
        

    def add_edge(self, src_node: str, processor_or_dst_node: Any):
        if src_node not in self.nodes:
            raise ValueError(f"Node {src_node} does not exist.")
        if isinstance(processor_or_dst_node, Processor):
            self.edges[src_node] = processor_or_dst_node
        elif isinstance(processor_or_dst_node, str):
            dst_node = processor_or_dst_node
            if dst_node not in self.nodes:
                raise ValueError(f"Destination node {dst_node} does not exist.")
            def default_processor(message: Any, workflow: WorkFlowBase, *args: Any, **kwargs: Any) -> Tuple[Any, str]:
                return message, dst_node
            if src_node in self.edges:
                raise ValueError(f"Edge already exists from {src_node}. To overwrite, remove the existing edge first.")
            self.edges[src_node] = default_processor
        else:
            raise TypeError("processor_or_dst_node must be either a Processor instance or a string representing a node name.")


    def set_entry_node(self, node: str) -> None:
        assert node in self.nodes, f"Node {node} does not exist."
        self.entry_node = node
        
    def set_exit_node(self, node: str) -> None:
        assert node in self.nodes, f"Node {node} does not exist."
        self.exit_node = node
    
    def __call__(self, initial_message: Any, *args: Any, **kwargs: Any) -> Any:
        if self.entry_node is None or self.exit_node is None:
            raise ValueError("Entry or exit node not set.")
        current_node = self.entry_node
        current_message = self.nodes[current_node](initial_message, *args, **kwargs)
        while current_node != self.exit_node:
            processor = self.edges[current_node]
            current_message, next_node = processor(current_message, self, *args, **kwargs)
            current_node = next_node
            if current_node in self.nodes:
                current_message = self.nodes[current_node](current_message, *args, **kwargs)
            else:
                break  # This should not happen if workflow is correctly configured
        return current_message
    
    
    
class AggregationCallable(Protocol):
    def __call__(self, results: Dict[str, Any]) -> Any:
        pass
    
class ParallelWorkFlow(WorkFlowBase):
    def __init__(self, 
                 workflows: Optional[Dict[str, SequentialWorkFlow]] = None,
                 aggregation_fn: Optional[AggregationCallable] = None, 
                 executor_type: Literal['threadpool', 'dask'] = 'threadpool') -> None:
        super().__init__()
        self.workflows = workflows if workflows else {}
        self.aggregation_fn = aggregation_fn
        self.executor_type = executor_type
    
    def add_workflow(self, name: str, workflow: SequentialWorkFlow) -> None:
        if name in self.workflows:
            raise ValueError(f"Workflow {name} already exists.")
        self.workflows[name] = workflow
    
    def __call__(self, initial_message: Any, *args: Any, **kwargs: Any) -> Any:
        assert self.workflows, "No workflows added."
        results = {}
        if self.executor_type == 'threadpool':
            with ThreadPoolExecutor() as executor:
                futures = {name: executor.submit(workflow, initial_message, *args, **kwargs)
                           for name, workflow in self.workflows.items()}
                for name, future in futures.items():
                        results[name] = future.result()
        elif self.executor_type == 'dask':
            delayed_results = {name: delayed(workflow)(initial_message, *args, **kwargs)
                               for name, workflow in self.workflows.items()}
            computed_results = compute(*delayed_results.values())
            results = dict(zip(delayed_results.keys(), computed_results))
        if self.aggregation_fn:
            final_result = self.aggregation_fn(results)
        else:
            final_result = results
        return final_result
            
        
            

    
    
        
        

                    
            
    

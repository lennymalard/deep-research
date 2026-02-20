from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage
from langchain_ollama import ChatOllama
import logging
from langgraph.types import Send
from datetime import datetime

from prompts import *
from states import *
from utils import SearchWrapper, create_vector_store, get_top_k, save_report

logging.basicConfig(level=logging.INFO)

current_date = datetime.now()

class QueryGenerator:
    def __init__(self, model: str = "qwen3:8b"):
        self.llm = ChatOllama(
            model=model,
            num_predict=4096,
            format="json"
        )
        self.structured_llm = self.llm.with_structured_output(GenerateQueries)
        self.system_prompt = GENERATE_QUERIES_PROMPT

    def generate_queries(self, state: QueryGeneratorState):
        logging.info("Entered in the 'generate_queries' node")
        search_iteration = state.get("search_iteration", 0) + 1
        prompt = [
            SystemMessage(self.system_prompt),
            SystemMessage(f"[USER QUERY]: {state["user_query"]}"),
            SystemMessage(f"[CURRENT DATE AND TIME]: {current_date}")
        ]
        response = GenerateQueries(
            search_queries=[
                QueryItem(query="", reason="The query generation has failed.")
            ]
        )
        for _ in range(5):
            try:
                response = self.structured_llm.invoke(prompt)
                break
            except Exception as e:
                logging.info(e)
        search_queries = response.search_queries
        logging.info(f"search_queries: {search_queries}")
        return {"search_queries": search_queries, "search_iteration": search_iteration}

class Researcher:
    def __init__(self, model: str = "qwen3:8b", search_api: str = "ddgs"):
        self.llm = ChatOllama(
            model=model,
            num_predict=4096,
            format="json"
        )
        self.structured_llm = self.llm.with_structured_output(Summarize)
        self.system_prompt = SUMMARIZER_PROMPT
        self.search_api = SearchWrapper(api=search_api)

    def search(self, state: ResearcherState):
        logging.info("Entered in the 'search' node")
        search_query = state["search_query"]
        urls, snippets = zip(*self.search_api.fetch(query=search_query))
        existing_urls = [result["url"] for result in state["search_results"]] if state["search_results"] else []
        scraped_data = [{"url": url, "content": self.search_api.scrape(url)} for url in urls if url not in existing_urls]
        if not scraped_data:
            logging.warning(f"No new content found for query: {search_query}")
            return {"summaries": [], "search_results": []}
        vector_store =  create_vector_store(web_pages=scraped_data, snippets_size=5000)
        top_k_snippets = get_top_k(query=state["user_query"], vector_store=vector_store, k=3)
        summaries = []
        for snippet in top_k_snippets:
            for _ in range(5):
                try:
                    url = snippet.metadata["url"]
                    content = snippet.page_content
                    prompt = [
                        SystemMessage(self.system_prompt),
                        SystemMessage(f"[CURRENT DATE AND TIME]: {current_date}"),
                        SystemMessage(f"[USER QUERY]: {state["user_query"]}"),
                        SystemMessage(f"[URL]: {url}"),
                        SystemMessage(f"[PAGE SNIPPET]: {content}")
                    ]
                    response = self.structured_llm.invoke(prompt)
                    summaries.append({"url": url, "summary": response.summary})
                    break
                except Exception as e:
                    logging.info(e)
        logging.info(f"search_results: {scraped_data}")
        logging.info(f"summaries: {summaries}")
        return {"summaries": summaries, "search_results": scraped_data}

class Reviewer:
    def __init__(self, model: str = "qwen3:8b"):
        self.llm = ChatOllama(
            model=model,
            format="json"
        )
        self.structured_llm = self.llm.with_structured_output(Review)
        self.system_prompt = REVIEWER_PROMPT

    def is_search_complete(self, state: SystemState):
        logging.info(f"review: {state["review"]}")
        if state["review"]["is_search_complete"]:
            return True
        else:
            return False

    def review(self, state: ReviewerState):
        logging.info("Entered in the 'review' node")
        search_iteration = state["search_iteration"]
        response = Review(is_search_complete=False, justification="An error occurred during review.")
        for _ in range(5):
            try:
                prompt = [
                    SystemMessage(self.system_prompt),
                    SystemMessage(f"[CURRENT DATE AND TIME]: {current_date}"),
                    SystemMessage(f"[USER QUERY]: {state["user_query"]}"),
                    SystemMessage(f"[SUMMARIES]: {state["summaries"]}"),
                    SystemMessage(f"[SEARCH ITERATION]: {state["search_iteration"]}")
                ]
                response = self.structured_llm.invoke(prompt)
                break
            except Exception as e:
                logging.info(e)
        if search_iteration >= 3:
            is_search_complete = True
            justification = "Maximum search iteration reached. " + response.justification
        else:
            is_search_complete = response.is_search_complete
            justification = response.justification
        logging.info(f"is_search_complete: {is_search_complete}")
        logging.info(f"justification: {justification}")
        return {"review": {"is_search_complete": is_search_complete, "justification": justification}}

class Writer:
    # TODO Create a citation tool ?
    def __init__(self, model: str = "qwen3:14b"):
        self.llm = ChatOllama(
            model=model,
            format="json"
        )
        self.structured_llm = self.llm.with_structured_output(Write)
        self.system_prompt = WRITER_PROMPT

    def write(self, state: WriterState):
        logging.info("Entered in the 'write' node")
        response = Review(is_search_complete=False, justification="An error occurred during review.")
        for _ in range(5):
            try:
                prompt = [
                    SystemMessage(self.system_prompt),
                    SystemMessage(f"[CURRENT DATE AND TIME]: {current_date}"),
                    SystemMessage(f"[USER QUERY]: {state["user_query"]}"),
                    SystemMessage(f"[SUMMARIES]: {state["summaries"]}")
                ]
                response = self.structured_llm.invoke(prompt)
                break
            except Exception as e:
                logging.info(e)
        report = response.report
        confidence = response.confidence
        logging.info(f"report: {report}")
        logging.info(f"confidence: {confidence}")
        return {"reports": [{"report": report, "confidence": confidence}]}

class Evaluator:
    def __init__(self, model: str = "qwen3:14b"):
        self.llm = ChatOllama(
            model=model,
            format="json"
        )
        self.structured_llm = self.llm.with_structured_output(Evaluate)
        self.system_prompt = EVALUATOR_PROMPT

    def get_best_report_index(self, marks: List[EvaluationItem]):
        return max(marks, key= lambda report: sum((report.faithfulness, report.answer_relevance, report.context_completeness, report.formatting_quality, report.synthesis_quality))).report_index

    def evaluate(self, state: EvaluatorState):
        logging.info("Entered in the 'evaluate' node")
        response = Evaluate(marks=[])
        indexed_reports = [
            {"index": i, "report": report_data["report"], "confidence": report_data["confidence"]}
            for i, report_data in enumerate(state["reports"])
        ]
        for _ in range(5):
            try:
                prompt = [
                    SystemMessage(self.system_prompt),
                    SystemMessage(f"[CURRENT DATE AND TIME]: {current_date}"),
                    SystemMessage(f"[USER QUERY]: {state["user_query"]}"),
                    SystemMessage(f"[SUMMARIES]: {state["summaries"]}"),
                    SystemMessage(f"[REPORTS]: {indexed_reports}")
                ]
                response = self.structured_llm.invoke(prompt)
                break
            except Exception as e:
                logging.info(e)
        marks = response.marks
        best_report_index = 0
        try:
            best_report_index = self.get_best_report_index(marks)
            final_report = state["reports"][best_report_index]["report"]
        except IndexError as e:
            logging.info(e)
            final_report = state["reports"][best_report_index]["report"]
        logging.info(f"marks: {marks}")
        logging.info(f"final_report: {final_report}")
        return {"final_report": final_report}

def route_plan_to_search(state: SystemState):
    return [Send("search", {"search_query": query_item.query, "user_query": state["user_query"], "search_results": state["search_results"] if "search_results" in state.keys() else []}) for query_item in state["search_queries"]]

def route_after_review(state: SystemState):
    is_search_complete = reviewer.is_search_complete(state)

    if is_search_complete:
        return [Send("write", {
            "summaries": state.get("summaries", []),
            "user_query": state["user_query"]
        }) for _ in range(5)]
    else:
        return "generate_queries"

query_generator = QueryGenerator()
researcher = Researcher()
reviewer = Reviewer()
writer = Writer()
evaluator = Evaluator()

graph = StateGraph(SystemState)

graph.add_node("generate_queries", query_generator.generate_queries)
graph.add_node("search", researcher.search)
graph.add_node("review", reviewer.review)
graph.add_node("write", writer.write)
graph.add_node("evaluate", evaluator.evaluate)

graph.add_conditional_edges(
    "generate_queries",
    route_plan_to_search,
    ["search"]
)

graph.add_edge("search", "review")
graph.add_conditional_edges(
    "review",
    route_after_review,
    ["write", "generate_queries"]
)
graph.add_edge("write", "evaluate")
graph.add_edge("evaluate", END)

graph.set_entry_point("generate_queries")
graph = graph.compile()

"""user_query = "Qui est le directeur artistique de Versace ?"

state: SystemState = {
    "user_query": user_query,
}

final_state = graph.invoke(state)

report = final_state["final_report"]
print(report)
save_report(user_query=user_query,report=report, file_name="report")"""
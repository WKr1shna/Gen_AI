"""
Enhanced Token Tracking and Real-Time Presentation Engine.
Captures per-call and cumulative metrics across intent classification and response generation,
and renders a rich dashboard in the terminal.
"""

import time
from typing import Dict, List, Optional, Any
from langchain_core.callbacks import BaseCallbackHandler

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich import box
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None


class TokenUsageCallbackHandler(BaseCallbackHandler):
    """
    LangChain callback handler to capture token usage per LLM invocation.
    Accurately records input, output, and total tokens from usage metadata.
    """
    def __init__(self, tracker: "TokenTracker"):
        super().__init__()
        self.tracker = tracker

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        pass

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        call_prompt_tokens = 0
        call_completion_tokens = 0
        call_total_tokens = 0
        model_name = "gemini-3.6-flash"

        if hasattr(response, "llm_output") and response.llm_output:
            usage = response.llm_output.get("token_usage", {})
            call_prompt_tokens = usage.get("prompt_tokens", 0)
            call_completion_tokens = usage.get("completion_tokens", 0)
            call_total_tokens = usage.get("total_tokens", 0)

        # Inspect generations for message usage metadata
        for gen_list in getattr(response, "generations", []):
            for gen in gen_list:
                msg = getattr(gen, "message", None)
                if msg:
                    usage = getattr(msg, "usage_metadata", None)
                    if usage:
                        call_prompt_tokens += usage.get("input_tokens", 0)
                        call_completion_tokens += usage.get("output_tokens", 0)
                        call_total_tokens += usage.get("total_tokens", 0)
                    
                    # Try to get model name if available
                    resp_metadata = getattr(msg, "response_metadata", {})
                    if "model_name" in resp_metadata:
                        model_name = resp_metadata["model_name"]

        self.tracker.record_llm_call(
            prompt_tokens=call_prompt_tokens,
            completion_tokens=call_completion_tokens,
            total_tokens=call_total_tokens,
            model_name=model_name
        )


class TokenTracker:
    """
    Comprehensive token and performance tracking engine.
    Maintains turn-scoped metrics and cumulative session statistics.
    """
    def __init__(self):
        # Current turn metrics
        self.current_turn_calls: List[Dict[str, Any]] = []
        self.turn_start_time: float = 0.0
        self.turn_latency: float = 0.0
        self.turn_route: str = "UNKNOWN"
        self.turn_input_text: str = ""
        self.turn_output_text: str = ""

        # Cumulative session statistics
        self.session_stats = {
            "total_requests": 0,
            "cumulative_prompt_tokens": 0,
            "cumulative_completion_tokens": 0,
            "cumulative_total_tokens": 0,
            "cumulative_words": 0,
            "routes_count": {
                "TOXIC": 0,
                "CODE_REQUEST": 0,
                "GENERAL": 0
            }
        }

    @property
    def callback_handler(self) -> TokenUsageCallbackHandler:
        """Return a callback handler linked to this tracker."""
        return TokenUsageCallbackHandler(self)

    def start_turn(self, input_text: str) -> None:
        """Initialize metrics collection for a new turn."""
        self.current_turn_calls = []
        self.turn_input_text = input_text
        self.turn_output_text = ""
        self.turn_route = "UNKNOWN"
        self.turn_start_time = time.perf_counter()

    def record_llm_call(self, prompt_tokens: int, completion_tokens: int, total_tokens: int, model_name: str = "gemini-3.8-flash") -> None:
        """Record an individual LLM call within the active turn."""
        # Infer phase: 1st call is typically classifier, 2nd is destination
        phase = "Intent Classifier" if len(self.current_turn_calls) == 0 else "Destination LLM"
        
        self.current_turn_calls.append({
            "phase": phase,
            "model": model_name,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens if total_tokens > 0 else (prompt_tokens + completion_tokens)
        })

    def end_turn(self, output_text: str, route: str) -> Dict[str, Any]:
        """Finalize the turn and update cumulative session metrics."""
        self.turn_latency = time.perf_counter() - self.turn_start_time
        self.turn_output_text = output_text
        self.turn_route = route.upper().strip()

        # Turn token totals
        turn_prompt = sum(call["prompt_tokens"] for call in self.current_turn_calls)
        turn_completion = sum(call["completion_tokens"] for call in self.current_turn_calls)
        turn_total = sum(call["total_tokens"] for call in self.current_turn_calls)

        # Word count metrics
        output_words = len(output_text.split()) if output_text else 0
        total_words = len(self.turn_input_text.split()) + output_words
        tokens_per_word = round(turn_total / output_words, 2) if output_words > 0 else 0.0

        # Update session totals
        self.session_stats["total_requests"] += 1
        self.session_stats["cumulative_prompt_tokens"] += turn_prompt
        self.session_stats["cumulative_completion_tokens"] += turn_completion
        self.session_stats["cumulative_total_tokens"] += turn_total
        self.session_stats["cumulative_words"] += output_words

        if self.turn_route in self.session_stats["routes_count"]:
            self.session_stats["routes_count"][self.turn_route] += 1
        else:
            self.session_stats["routes_count"][self.turn_route] = 1

        summary = {
            "latency": self.turn_latency,
            "route": self.turn_route,
            "prompt_tokens": turn_prompt,
            "completion_tokens": turn_completion,
            "total_tokens": turn_total,
            "output_words": output_words,
            "tokens_per_word": tokens_per_word,
            "calls": len(self.current_turn_calls),
            "calls_breakdown": list(self.current_turn_calls)
        }
        return summary

    def display_metrics(self) -> None:
        """Render a visually stunning presentation of token tracking and session metrics."""
        turn_prompt = sum(call["prompt_tokens"] for call in self.current_turn_calls)
        turn_completion = sum(call["completion_tokens"] for call in self.current_turn_calls)
        turn_total = sum(call["total_tokens"] for call in self.current_turn_calls)
        output_words = len(self.turn_output_text.split()) if self.turn_output_text else 0
        tokens_per_word = round(turn_total / output_words, 2) if output_words > 0 else 0.0

        req_num = self.session_stats["total_requests"]
        avg_tokens_req = (
            round(self.session_stats["cumulative_total_tokens"] / req_num, 2)
            if req_num > 0 else 0.0
        )
        avg_tokens_word = (
            round(self.session_stats["cumulative_total_tokens"] / self.session_stats["cumulative_words"], 2)
            if self.session_stats["cumulative_words"] > 0 else 0.0
        )

        if RICH_AVAILABLE:
            self._display_rich(
                turn_prompt=turn_prompt,
                turn_completion=turn_completion,
                turn_total=turn_total,
                output_words=output_words,
                tokens_per_word=tokens_per_word,
                req_num=req_num,
                avg_tokens_req=avg_tokens_req,
                avg_tokens_word=avg_tokens_word
            )
        else:
            self._display_ansi_fallback(
                turn_prompt=turn_prompt,
                turn_completion=turn_completion,
                turn_total=turn_total,
                output_words=output_words,
                tokens_per_word=tokens_per_word,
                req_num=req_num,
                avg_tokens_req=avg_tokens_req,
                avg_tokens_word=avg_tokens_word
            )

    def _display_rich(self, turn_prompt: int, turn_completion: int, turn_total: int,
                      output_words: int, tokens_per_word: float, req_num: int,
                      avg_tokens_req: float, avg_tokens_word: float) -> None:
        """Rich terminal dashboard."""
        route_color = "red" if "TOXIC" in self.turn_route else "green" if "CODE" in self.turn_route else "yellow"
        route_icon = "🛑" if "TOXIC" in self.turn_route else "💻" if "CODE" in self.turn_route else "🚫"

        # Create Turn Breakdown Table
        table = Table(
            title=f"⚡ [bold cyan]Token & Resource Usage Analysis[/bold cyan] (Request #{req_num})",
            box=box.ROUNDED,
            header_style="bold magenta",
            border_style="cyan"
        )
        table.add_column("Pipeline Stage / Call", style="bold white", width=24)
        table.add_column("Prompt Tokens", justify="right", style="blue")
        table.add_column("Completion Tokens", justify="right", style="green")
        table.add_column("Total Tokens", justify="right", style="bold yellow")
        table.add_column("Share", justify="right", style="cyan")

        if self.current_turn_calls:
            for idx, call in enumerate(self.current_turn_calls, 1):
                share = f"{(call['total_tokens'] / turn_total * 100):.1f}%" if turn_total > 0 else "0%"
                table.add_row(
                    f"#{idx} {call['phase']}",
                    str(call["prompt_tokens"]),
                    str(call["completion_tokens"]),
                    str(call["total_tokens"]),
                    share
                )
        else:
            table.add_row("Direct Hardcoded Lambda", "0", "0", "0", "0%")

        # Add Turn Summary Row
        table.add_section()
        table.add_row(
            "[bold white]Turn Total[/bold white]",
            f"[bold blue]{turn_prompt}[/bold blue]",
            f"[bold green]{turn_completion}[/bold green]",
            f"[bold yellow]{turn_total}[/bold yellow]",
            "[bold cyan]100%[/bold cyan]"
        )

        console.print("\n")
        console.print(table)

        # Efficiency & Latency Metric Cards
        metrics_text = Text()
        metrics_text.append(f"⏱️  Latency: {self.turn_latency:.3f}s   │   ", style="bold white")
        metrics_text.append(f"📝 Output: {output_words} words   │   ", style="bold white")
        metrics_text.append(f"🎯 Density: {tokens_per_word} tokens/word   │   ", style="bold white")
        metrics_text.append(f"🛣️  Route: {route_icon} {self.turn_route}", style=f"bold {route_color}")

        console.print(Panel(metrics_text, title="[bold cyan]Turn Performance[/bold cyan]", border_style="blue", box=box.ROUNDED))

        # Session Cumulative Panel
        routes_summary = "  ".join([f"{k}: {v}" for k, v in self.session_stats["routes_count"].items() if v > 0])
        session_text = (
            f"📊 [bold]Session Requests:[/bold] {req_num} total   │   "
            f"⚡ [bold]Cumulative Tokens:[/bold] {self.session_stats['cumulative_total_tokens']} "
            f"([blue]{self.session_stats['cumulative_prompt_tokens']} prompt[/blue] + [green]{self.session_stats['cumulative_completion_tokens']} completion[/green])\n"
            f"📈 [bold]Averages:[/bold] {avg_tokens_req} tokens/req   •   {avg_tokens_word} tokens/word   │   "
            f"🚦 [bold]Routes Distribution:[/bold] {routes_summary}"
        )
        console.print(Panel(session_text, title="[bold magenta]Cumulative Session Analytics[/bold magenta]", border_style="magenta", box=box.ROUNDED))
        console.print("\n" + "─" * 70)

    def _display_ansi_fallback(self, turn_prompt: int, turn_completion: int, turn_total: int,
                               output_words: int, tokens_per_word: float, req_num: int,
                               avg_tokens_req: float, avg_tokens_word: float) -> None:
        """Unicode / ANSI formatted metrics display fallback."""
        print("\n" + "=" * 68)
        print(f" 📊 [TOKEN & RESOURCE METRICS] Turn #{req_num} (Route: {self.turn_route})")
        print("=" * 68)
        print(f"  ⏱️  Latency:           {self.turn_latency:.4f}s")
        print(f"  ⚡ Turn Tokens:       {turn_total} total ({turn_prompt} prompt + {turn_completion} completion)")
        print(f"  📝 Output Words:       {output_words} words")
        print(f"  🎯 Tokens Per Word:    {tokens_per_word} t/w")
        print("  " + "-" * 64)
        for idx, call in enumerate(self.current_turn_calls, 1):
            print(f"     Call #{idx} [{call['phase']}]: {call['total_tokens']} tokens ({call['prompt_tokens']} in, {call['completion_tokens']} out)")
        print("  " + "-" * 64)
        print(f"  📈 Session Cumulative: {self.session_stats['cumulative_total_tokens']} tokens across {req_num} requests")
        print(f"  📊 Avg Tokens/Req:     {avg_tokens_req} tokens/request")
        print(f"  📊 Avg Tokens/Word:    {avg_tokens_word} tokens/word")
        print("=" * 68 + "\n")

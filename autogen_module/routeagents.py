# autogen_module/routeagents.py - Fixed Version
import json
import asyncio
import sys
import os
from typing import List, Dict, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from autogen_module.agents import all_agents, USER_PROXY_NAME, SEARCHER_NAME, EXPERT_ADVISOR_NAME
from config import autogen_llm_config_list
from autogen_module.userdata_agent import user_data_agent_wrapper
import autogen
import tiktoken

class AgentRouter:
    def __init__(self):
        self.all_agents = {agent.name: agent for agent in all_agents}
        self.router_agent = self._create_simple_router_agent()
    
    def count_tokens(self, text, model: str = "gpt-4") -> int:
        """Count tokens using tiktoken"""
        try:
            # Convert to string if it's not already
            if not isinstance(text, str):
                text = str(text)
            
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception:
            # If any error occurs, return 0 tokens
            return 0

    def _create_simple_router_agent(self):
        """Create simple routing agent that returns specialist name directly"""
        return autogen.AssistantAgent(
            name="AgentRouter",
            llm_config={
                "config_list": autogen_llm_config_list,
                "temperature": 0.0
            },
            system_message="You are the router. You will be given the user's message, image description (if any), and distilled context/memories. Return ONLY a JSON array of 1–3 case-sensitive names chosen from [SoilScienceSpecialist, PlantNutritionExpert, WeatherSpecialist, LivestockBreedSpecialist, UserDataAgent, DefaultAgent]. Routing rules: DefaultAgent - greetings/chit-chat/general questions, queries answerable from context/memories, declarative statements/personal facts, and follow-ups with no new domain ask. UserDataAgent - explicit CRUD/read on profile/contact fields ONLY (FirstName, MiddleInitial, LastName, Phone, Cell, Fax, Email, UserName, Bio). Soil/Plant/Weather/Livestock - only when the user requests advice/analysis/recommendations in that domain; prefer DefaultAgent for any general statements. Multi-topic: include each applicable specialist (max 3). If uncertain, return [\"DefaultAgent\"]. Output must be valid JSON ONLY (no explanations), e.g., [\"DefaultAgent\"]."
        )
    
    async def process_query(self, query: str, websocket=None) -> Dict:
        """Main entry point - processes query and returns final response"""
        try:
            total_tokens = 0
            
            # Step 1: Route to select specialist
            selected_specialist = await self._route_specialist(query)
            
            # Count routing tokens
            routing_input = f"Which specialist is needed for: {query}"
            total_tokens += self.count_tokens(routing_input)
            total_tokens += self.count_tokens(str(selected_specialist))
            
            # Step 2: Execute selected specialist chain
            response, specialist_tokens = await self._execute_specialist_chain(selected_specialist, query, websocket)
            total_tokens += specialist_tokens
            
            print(f"🔢 Total tokens used for this request: {total_tokens}")

            print("response", response)
            
            return {
                "success": True,
                "final_response": response,
                "specialist_used": selected_specialist,
                "total_tokens": total_tokens
            }
            
        except Exception as e:
            print(f"❌ Error in agent processing: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "final_response": "I apologize, but I encountered an error processing your request. Please try again."
            }
    
    async def _route_specialist(self, query: str) -> str:
        """Simple routing - just parse the response text"""
        
        print(f"🔄 Routing query: {query}")
        
        try:
            router_agent_response = self.router_agent.generate_reply([{
                "role": "user",
                "content": f"Which specialist is needed for: {query}"
            }])
            print("router_agent_response", router_agent_response)
            # specialist_names = router_agent_response.strip().split(',')
            # specialist_names_list = [name.strip() for name in specialist_names]
            specialist_names_list = json.loads(router_agent_response)

            print("specialist_names_list", specialist_names_list)
            
            # Validate the specialist name
            valid_specialists = [
                "SoilScienceSpecialist",
                "PlantNutritionExpert",
                "WeatherSpecialist",
                "LivestockBreedSpecialist",
                "UserDataAgent",
                "DefaultAgent"
            ]

            valid_selected = [name for name in specialist_names_list if name in valid_specialists]

            if valid_selected:
                print(f"✅ Selected specialist: {specialist_names_list}")
                return specialist_names_list
            else:
                # Fallback to default if invalid response
                print(f"⚠️ No valid specialists found in '{router_agent_response}', using DefaultAgent")
                return ["DefaultAgent"]
                
        except Exception as e:
            print(f"❌ Error in routing: {e}")
            return ["DefaultAgent"]
    
    async def _execute_specialist_chain(self, specialist_names: list, query: str, websocket=None) -> tuple[str, int]:
        """Execute the selected specialist(s) and use expert advisor for multiple specialists"""
        specialist_responses = []
        chain_tokens = 0
        
        # Count initial query tokens
        chain_tokens += self.count_tokens(query)
        
        # Execute agents in chain
        for specialist_name in specialist_names:
            if websocket:
                await self._send_agent_step(websocket, specialist_name)
            try:
                agent = self.all_agents.get(specialist_name, self.all_agents.get("DefaultAgent"))
                
                # Special handling for UserDataAgent to use the wrapper
                if specialist_name == "UserDataAgent":
                    # Pass the full enhanced message to UserDataAgent so it can extract USER ID
                    response = user_data_agent_wrapper.generate_reply(agent, [{
                        "role": "user",
                        "content": query  # Pass the full enhanced message
                    }])
                # In the else block where you handle non-UserDataAgent
                else:
                    response = agent.generate_reply([{
                        "role": "user",
                        "content": query
                    }])
                    
                    # Check if response is a dict with tool calls (function execution failed)
                    if isinstance(response, dict) and 'tool_calls' in str(response):
                        print("🔧 Manual function execution needed...")
                        
                        # Extract and execute the function call manually
                        if specialist_name == "WeatherSpecialist":
                            # Parse the zipcode from the tool call
                            import json
                            tool_call = response.get('tool_calls', [{}])[0]
                            args = json.loads(tool_call.get('function', {}).get('arguments', '{}'))
                            zipcode = args.get('zipcode', '')
                            
                            if zipcode:
                                # Call the function directly
                                from autogen_module.agents import get_weather_report_for_zipcode
                                response = get_weather_report_for_zipcode(zipcode)
                                print(f"✅ Manual function execution successful")
                            else:
                                response = "Could not extract zip code from the request."
                
                # Count tokens for this specialist
                chain_tokens += self.count_tokens(query)  # Input to specialist
                chain_tokens += self.count_tokens(response)  # Output from specialist
                
                print(f"✅ {specialist_name} completed")
                specialist_responses.append(f"**{specialist_name}**: {response}")
                
            except Exception as e:
                print(f"❌ Error executing {specialist_name}: {e}")
                return "I apologize, but I encountered an error processing your request.", chain_tokens
        
        # If more than 1 specialist was used, involve the expert advisor
        # BUT skip Expert Advisor for UserDataAgent responses (they're not agricultural)
        if len(specialist_names) > 1 and "UserDataAgent" not in specialist_names:
            print(f"🎯 Multiple specialists used ({len(specialist_names)}), consulting Expert Advisor...")
            
            if websocket:
                await self._send_agent_step(websocket, EXPERT_ADVISOR_NAME)
            
            try:
                # Create a comprehensive summary for the Expert Advisor
                combined_analysis = f"""
                Original Query: {query}

                Specialist Analysis:
                {chr(10).join(specialist_responses)}
                """
                
                # Count tokens for Expert Advisor input
                chain_tokens += self.count_tokens(combined_analysis)
                
                expert_advisor = self.all_agents.get(EXPERT_ADVISOR_NAME, self.all_agents.get("DefaultAgent"))
                final_response = expert_advisor.generate_reply([{
                    "role": "user",
                    "content": combined_analysis
                }])
                
                # Count tokens for Expert Advisor output
                chain_tokens += self.count_tokens(final_response)
                
                print(f"✅ {EXPERT_ADVISOR_NAME} synthesis completed")
                return final_response, chain_tokens
                
            except Exception as e:
                print(f"❌ Error with {EXPERT_ADVISOR_NAME}: {e}")
                # Fallback to combined specialist responses if expert advisor fails
                fallback_response = f"Here are the specialist analyses:\n\n{chr(10).join(specialist_responses)}"
                return fallback_response, chain_tokens
            
        elif "UserDataAgent" in specialist_names:
            # For UserDataAgent, return the response directly without Expert Advisor
            print(f"🎯 UserDataAgent used, returning response directly...")
            user_data_response = specialist_responses[0].replace("**", "").split(": ", 1)[1] if specialist_responses else "I apologize, but I encountered an error processing your request."
            return user_data_response, chain_tokens
        
        else:
            # Single specialist - return their response directly
            single_response = specialist_responses[0].replace("**", "").split(": ", 1)[1] if specialist_responses else "I apologize, but I encountered an error processing your request."
            return single_response, chain_tokens
    
    async def _send_agent_step(self, websocket, agent_name: str):
        """Send agent step update to UI"""
        try:
            step_data = {
                "type": "agent_step",
                "agent_name": agent_name
            }
            await websocket.send_text(json.dumps(step_data))
            await asyncio.sleep(0.1)
        except Exception as e:
            print(f"❌ Error sending agent step: {e}")


# agent_router = AgentRouter()

# asyncio.run(agent_router.process_query("Hi!"))









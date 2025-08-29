from app.models.ChatHistory import ChatHistory
from app.models.PropertyLead import PropertySearchParams
from app.models.ChatState import MyState, ContentTypeMapping, InputRouter
from typing import List
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph
from app.services.stages.router_llm import get_route_chain, get_route_chain_v2
from app.services.stages.extract_chain import get_extract_chain
from app.models.ChatState import MyState
import json
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)



def proccess_chat_turn(user_id: str = '', conv_id:str = '', user_message:str = '', metadata:dict = {}, verbose:bool = False, get_graph:bool = False):
    # 1. Recuperar los mensajes históricos.
    # Necesitamos los siguientes datos para nuestro planner: 
    # previous_state + message_history + entities .

    chat_history = ChatHistory(user_id, conv_id)
    chat_history.get_messages(chat_history.context_length) #contacts dynamodb and retrieves messages.
    input_state  = dict(zip(['input_state', 'state_count'], chat_history.retrieve_current_stage()))
    input_lead = chat_history.retrieve_current_lead()
    message_history = chat_history.get_langchain_history()

    # Saving user message
    chat_history.add_message(
        content={'text': user_message},
        role= 'user',
        content_type='text',
        metadata={
            **metadata,
            "lead": json.dumps(input_lead.model_dump()),
            "state": input_state.get('input_state'),
            "conversation_length": chat_history.context_length+1
            }
    )

    # Workflow Definition
    workflow = StateGraph(MyState)
    
    # Node Creation
    workflow.add_node("input_router", run_input_route_v2) # Testing
    workflow.add_node("extract", run_extract)
    workflow.add_node("other", run_other)
    workflow.add_node("lead_router", run_lead_route)
    workflow.add_node("query_user", run_query_user)
    workflow.add_node("search_properties", run_search_properties)
    workflow.add_node("new_search", run_new_search)
    workflow.add_node("format_output", run_format_output)

    # conditionals
    workflow.add_conditional_edges(
        "input_router",       # nombre del nodo router
        lambda x: x.input_route_result['input_route_decision'],# función que retorna el nombre del siguiente nodo
        {"extract": "extract", "other": "other", "new_search": "new_search"}
    )

    workflow.add_conditional_edges(
        "lead_router",
        lambda x: x.lead_route_result,
        {"query_user": "query_user", "search_properties": "search_properties"}
    )


    # Node Connections
    workflow.set_entry_point("input_router")
    workflow.add_edge("extract", "lead_router")
    workflow.add_edge("new_search", "extract")
    workflow.add_edge("other", "format_output")
    workflow.add_edge("query_user", "format_output")
    workflow.add_edge("search_properties", "format_output")
    #workflow.set_finish_point("extract")

    # Workflow Invocation
    app = workflow.compile()

    #GetGraph Instead 
    if get_graph:
        print(app.get_graph().draw_mermaid())
        return

    response = app.invoke({
        "user_message": user_message,
        "input_lead": input_lead,
        "input_state": input_state,
        "message_history": message_history
    },
    verbose=True)

    # Context Length
    if response.get('new_search_flag', False) == True:
        current_context_length = 0
    else:
        current_context_length = chat_history.context_length
    

    final_state = response.get('final_output').get('final_state')
    # Saving result
    # bot message
    chat_history.add_message(
        content = response.get('final_output').get('content'),
        role = 'assistant',
        content_type = response.get('final_output').get('content_type'),
        metadata={
            "lead": response.get('final_output').get('lead'),
            "state": final_state,
            "conversation_length": current_context_length+2
        }
    )
    # guardado
    chat_history.save_new_messages()

    # LOGICA adicional para el frontend
    if final_state in ['other', 'query_user']:
        output_stage = 'extract'
        output_content = {'model_response': response.get('final_output').get('content').get('text')}
    else:
        output_stage = 'recommend'
        output_content = response.get('final_output').get('content').get('properties')

    if verbose:
        return output_stage, response
    else:
        return output_stage, output_content

# Node Function Definition
def run_input_route(state: MyState):
    """Input Router"""
    logger.info('Routing')
    result = get_route_chain().invoke(
        {
            "entities": str(json.dumps(state.input_lead.model_dump())).replace("{", "{{").replace("}","}}"),
            "input_state": str(state.input_state).replace("{", "{{").replace("}","}}"),
            "input": state.user_message,
            "message_history": state.message_history
        }
    )
    state.input_route_result['llm_raw_output'] = result
    state.input_route_result['input_route_decision'] = result.model_dump().get('content', 'error')
    state.current_state_flow.append(state.input_state.get('input_state'))
    return state

def run_input_route_v2(state: MyState):
    """Input Router w/ EnumOutputParser"""
    logger.info('Routing')
    try:
        result = get_route_chain_v2().invoke(
            {
                "entities": str(json.dumps(state.input_lead.model_dump())).replace("{", "{{").replace("}","}}"),
                "input_state": str(state.input_state).replace("{", "{{").replace("}","}}"),
                "user_message": state.user_message,
            }
        )
    except Exception as e:
        logger.error('route_v2: Failed to parse a valid route. Defaulting to "extract"')
        result = InputRouter.extract
    state.input_route_result['input_route_decision'] = result.value
    state.current_state_flow.append(state.input_state.get('input_state'))
    return state

def run_new_search(state: MyState):
    """New Search"""
    state.input_lead = PropertySearchParams()
    state.new_search_flag = True
    state.current_state_flow.append('new_search')    
    return state

def run_extract(state: MyState):
    """Extract Node"""
    result = get_extract_chain().invoke({
        "user_message": state.user_message,
        "input_lead": state.input_lead
    })
    state.extract_result['llm_raw_output'] = result['extract_llm_raw_output']
    state.extract_result['parsed_lead'] = result['extract_parsed_lead']
    state.extract_result['merged_lead'] = result['extract_merged_lead']
    state.current_state_flow.append('extract')
    return state

def run_lead_route(state: MyState):
    """Route decision after lead extraction"""
    lead = state.extract_result.get('merged_lead')
    last_state = state.input_state.get('input_state')
    last_state_count = state.input_state.get('state_count')

    # Route logic
    if lead.verify_lead() == False:
        state.lead_route_result = 'query_user'
    else:
        if last_state == 'refine' and  last_state_count <2:
            state.lead_route_result = 'query_user'
        else:
            state.lead_route_result = 'search_properties'
    return state

def run_query_user(state: MyState):
    """Call LLM and formulates questions for user"""
    from app.services.stages.query_user_chain import get_query_user_chain

    chat_history: List[BaseMessage] = state.message_history    #para contexto
    lead: PropertySearchParams = state.extract_result.get('merged_lead')
    
    #1. obtemos información para el prompt
    missing_values = str(lead.get_params_description(missing=True)).replace('{','{{').replace('}','}}')
    present_values = str(lead.get_params_description(missing=False)).replace('{','{{').replace('}','}}')

    #2. Obtenemos cadena.
    chain = get_query_user_chain()

    #3. Invocamos cadena.
    result = chain.invoke({
        "message_history": chat_history,
        "missing_values": missing_values,
        "present_values": present_values,
        "input": state.user_message
    })

    state.query_user_result["llm_raw_output"] = result
    state.query_user_result["user_query_output"] = result.model_dump().get('content', 'error')
    state.current_state_flow.append('query_user')
    return state

def run_search_properties(state: MyState)->list:
    """Searches properties"""
    from app.services.embeddings.search_opensearch import search_similar_properties
    try:
        logger.info('property_search: Starting')
        query = state.extract_result['merged_lead'].to_opensearch_query_knn_filtered(query_size = 5)
        recommendations = search_similar_properties(query)
        state.search_properties_result = recommendations
    except Exception as e:
        logger.error(f'property_search: Failed. Detail: {e}')
        state.search_properties_result = ['error',]
    state.current_state_flow.append('search_properties')
    return state

def run_other(state: MyState):
    """Other Node"""
    state.other_result = 'Lo siento, solo resolvemos dudas asociadas a búsqueda de propiedades inmobiliarias'
    state.new_search_flag = True
    state.current_state_flow.append('other')
    return state

def run_format_output(state: MyState):
    """Formats final output"""


    final_state = state.current_state_flow[-1]
    content_type = getattr(ContentTypeMapping, final_state).value
    # final_state_response
    final_state_response = getattr(state, final_state +"_result")
    match final_state:
        case 'other':
            content = {"text": final_state_response} # str
        case 'query_user':
            content = {"text": final_state_response.get('user_query_output')} # str
        case 'search_properties':
            content = {'properties': final_state_response} # list of properties
    lead: PropertySearchParams = getattr(state, 'extract_result', {}).get('merged_lead', PropertySearchParams())

    final_output = {
        "final_state": final_state,
        "content_type": content_type,
        "content": content,
        "lead": json.dumps(lead.model_dump())
                    }
    
    state.final_output = final_output

    return state
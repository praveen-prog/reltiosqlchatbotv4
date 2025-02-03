import os
import sys
from langchain_community.utilities import SQLDatabase
from entity.config_entity import SetUpConfig
from logger import logging
from langchain_openai import ChatOpenAI
from langchain.chains import create_sql_query_chain
from exception import sqlboterror
from langchain_core.output_parsers.openai_tools import PydanticToolsParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from prompt import *        
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from operator import itemgetter
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from typing import List 
from langchain_core.runnables import RunnableLambda   
from langchain.memory import ConversationBufferMemory
import warnings
from sqlalchemy import exc
warnings.filterwarnings("ignore", category=exc.SAWarning)

class DBConnectClass: 
    def __init__(self):
        pass

    def connect_chinook_info(self,setupconfig : SetUpConfig = SetUpConfig() ):
        try:    
            """Connects to the Chinook database using the provided URI and prints dialect and table names."""
            self.setupconfig = setupconfig

            self.db = SQLDatabase.from_uri(self.setupconfig.database_name)

            logging.info(f"Dialect: {self.db.dialect}")
            logging.info(f"Usable Table Names: {self.db.get_usable_table_names()}")
            #logging.info(self.db.run("SELECT * FROM Artist LIMIT 10;"))
            logging.info(f"Connected to Chinook DB {self.db}")
            logging.info(f"Populatingt the keys {self.setupconfig.langchain_tracing_v2}")
            os.environ["LANGCHAIN_TRACING_V2"] = self.setupconfig.langchain_tracing_v2
            os.environ["LANGCHAIN_API_KEY"] = self.setupconfig.langchain_api_key
            os.environ["OPENAI_API_KEY"] = self.setupconfig.openai_api_key
            logging.info(f"Getting model info")
            self.llm = ChatOpenAI(model=self.setupconfig.model_name)
            logging.info(f"Model is {self.llm} ")

            db = self.db
            llm = self.llm

            return  db , llm
        except Exception as e:
            raise sqlboterror(e,sys)  




class CategoryClass(BaseModel):
    """Table in SQL database."""

    name: str = Field(description="Name of table in SQL database.")

    def category_chain_call(self):
        try:
            logging.info("Inside Category chain creation method")
            DBConnectClass.connect_chinook_info(self)
            logging.info("Initiating the chain")
            chain = create_sql_query_chain(self.llm, self.db)
            logging.info(f"Initiated chain is {chain}")
            table_names = "\n".join(self.db.get_usable_table_names())
            logging.info(f"Fetching table names{table_names}")


            system = f"""Return the names of ALL the SQL tables that MIGHT be relevant to the user question. \
            The tables are:

            {table_names}

            Remember to include ALL POTENTIALLY RELEVANT tables, even if you're not sure that they're needed."""

            prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                ("human", "{input}"),
            ]
                )

            logging.info(f"prompt is {prompt}")
            
        except Exception as e:
            raise sqlboterror(e,sys)  
        
class TableCallClass(BaseModel):
    def __init__(self):
        pass

    def table_call(self):
        try:
            db_connect = DBConnectClass()
            db, llm = db_connect.connect_chinook_info()
            logging.info(f"{db}")
            logging.info(f"{llm}")

            llm_with_tools = llm.bind_tools([CategoryClass])
            output_parser = PydanticToolsParser(tools=[CategoryClass])
            logging.info(f" llm with tools is {llm_with_tools}")

            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", system_category_prompt),
                    ("human", "{input}"),
                ]
            )

            category_chain = prompt | llm_with_tools | output_parser
            #category_value = category_chain.invoke({"input": "What are all the genres of Alanis Morisette songs"})
            #logging.info(f"Catgeory value is {category_value}")
            return category_chain
    
        except Exception as e:
            raise sqlboterror(e,sys)   
        
    

class TableListClass():
    def __init__(self):
        pass     

    def get_tables(self,categories: List[CategoryClass]) -> List[str]:
        tables = []
        for category in categories:
            if category.name == "Music":
                tables.extend(
                    [
                        "Album",
                        "Artist",
                        "Genre",
                        "MediaType",
                        "Playlist",
                        "PlaylistTrack",
                        "Track",
                    ]
                )
            elif category.name == "Business":
                tables.extend(["Customer", "Employee", "Invoice", "InvoiceLine"])
            elif category.name == "Hospital":
                tables.extend(["HealthCareProvider","Patient","HospitalDepartment","PatientAdmissionHistory","StaffUtilization"])    
        return tables
    
    def table_detail_list_call(self):
        try:
            logging.info("Creating list of tables needed")
            table_call = TableCallClass()
            get_tables_call = TableListClass()
            table_chain = table_call.table_call() | get_tables_call.get_tables
            table_detail_list = table_chain.invoke({"input": "What are all the genres of Alanis Morisette songs"})   
            logging.info(f"Created list of tables needed. {table_detail_list}")
            return table_chain

        except Exception as e:
            raise sqlboterror(e,sys)   
    
    def parse_final_answer(self,output: str) -> str:
        return output.split("Final answer: ")[1]
    
    def full_chain_call(self, user_query):
        try:
            logging.info("Entered Full chain call method")
            db_connect = DBConnectClass()
            db, llm = db_connect.connect_chinook_info()

            # Initialize memory
            memory = ConversationBufferMemory(input_key="question", memory_key="chat_history")

            # Wrap parse_final_answer as RunnableLambda
            parse_final_answer_runnable = RunnableLambda(lambda x: self.parse_final_answer(x))

            # Prompt template with memory integration
            prompt = ChatPromptTemplate.from_messages(
                [("system", system_sql_prompt), ("human", "{input}")]
            ).partial(dialect=db.dialect)

            # Create chain with runnable parse_final_answer
            full_chain = create_sql_query_chain(llm, db, prompt=prompt) | parse_final_answer_runnable
            execute_query = QuerySQLDataBaseTool(db=db, use_query_checker=True, response_format='content')
            write_query = full_chain

            # Answer prompt
            answer_prompt = PromptTemplate.from_template(
                """Given the following user question, corresponding SQL query, and SQL result, answer the user question.

                Question: {question}
                SQL Query: {query}
                SQL Result: {result}
                Answer: """
            )

            # Add memory to table_chain
            table_chain_detail = self.table_detail_list_call()
            table_chain = {"input": itemgetter("question")} | table_chain_detail

            # Integrate memory into chain
            chain = (
                RunnablePassthrough.assign(query=write_query, table_names_to_use=table_chain)
                .assign(result=itemgetter("query") | execute_query)
                | answer_prompt
                | llm
                | StrOutputParser()
            )

            # Include memory interaction

            response = chain.invoke(
                {"question": user_query, "chat_history": memory.load_memory_variables({})}
            )
            
            # Save interaction to memory
            memory.save_context({"question": user_query}, {"response": response})
            
            print(response)
            logging.info(f"Output is {response}")

            return response

        except Exception as e:
            raise sqlboterror(e, sys)
        
#obj =    TableListClass()
#user_query = input("Enter user query : " )
#obj.full_chain_call(user_query)

# obj.table_detail_list_call()

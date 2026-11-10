from langchain_core.runnables import RunnableLambda

# runable架构

def add(x: int) -> int:
    return x + 1

def multiply(x: int) -> int:
    return x * 2

def main():
    add_runnable = RunnableLambda(add)
    multiply_runnable = RunnableLambda(multiply)
    chain = add_runnable | multiply_runnable   # 先调用加再调用减
    result = chain.invoke(10)
    print("result:", result)

if __name__ == "__main__":
    main()

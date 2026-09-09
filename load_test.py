import httpx
import asyncio
import time

URL = "http://127.0.0.1:8000/login"
USERNAME = "saurabh"
PASSWORD = "123456"

CONCURRENCY = 10
TOTAL_REQUESTS = 100


async def send_request(client, url, username, password):
    start_time = time.perf_counter()

    response = await client.get(
        url,
        params={
            "username": username,
            "password": password
        }
    )

    end_time = time.perf_counter()

    latency = (end_time - start_time) * 1000

    return latency, response.json(), response.status_code


async def run_load_test(total_requests, concurrency):

    semaphore = asyncio.Semaphore(concurrency)

    async with httpx.AsyncClient() as client:

        async def worker():
            async with semaphore:
                return await send_request(
                    client,
                    URL,
                    USERNAME,
                    PASSWORD
                )

        tasks = []

        for _ in range(total_requests):
            task = asyncio.create_task(worker())
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        sucess=0
        fialed=0
        for result in results:
            if result[2]==200:
                sucess+=1
            else:
                fialed+=1

        return results
    

def calculate_percentiles(results):
       
    latencies=[]
   
    for lantency,response,status_code in results:
        latencies.append(lantency)
    latencies.sort()
    p95_index = int(len(latencies) * 0.95) - 1
    p99_index = int(len(latencies) * 0.99) - 1

    p95 = latencies[p95_index]
    p99 = latencies[p99_index]
    return p95, p99


async def main():

    start_time = time.perf_counter()

    results = await run_load_test(
        TOTAL_REQUESTS,
        CONCURRENCY
    )

    end_time = time.perf_counter()
    print("""
    
========================================
            API STRESS LAB
========================================
""")
    print("Total requests:", TOTAL_REQUESTS)
    print("Concurrency level:", CONCURRENCY)
    print("Total results:", len(results))
    print("Total test time:", end_time - start_time, "seconds")
    print("Successful requests:", sum(1 for r in results if r[2] == 200))
    print("Failed requests:", sum(1 for r in results if r[2] != 200))
    p95, p99 = calculate_percentiles(results)
    print("P95:", p95, "ms")
    print("P99:", p99, "ms")        

    for result in results[:5]:
        print(result)


asyncio.run(main())
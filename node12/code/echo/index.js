function handler(event) {
    event["function_timestamp"] = new Date().getTime()
    return event
}
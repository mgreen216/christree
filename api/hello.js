// api/hello.js
export default function handler(request, response) {
  console.log("--- Node.js hello function invoked ---");
  response.status(200).json({ message: 'Hello from Node!' });
}

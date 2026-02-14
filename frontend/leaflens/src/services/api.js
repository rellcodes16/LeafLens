import axios from "axios";

const API = axios.create({
  baseURL: "http://localhost:8000",
});

export const searchByText = async (text) => {
  const res = await API.post("/text-search", { text });
  return res.data;
};

export const searchByImage = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  const res = await API.post("/image-search", formData);
  console.log(res.data)
  return res.data;
};

import { describe, it, expect } from "vitest";
import FormModel from "../../src/models/Form";

function formDataToObject(formData) {
  const obj = {};
  for (const [key, value] of formData.entries()) {
    obj[key] = value;
  }
  return obj;
}

describe("FormModel.toFormData", () => {
  it("converte um objeto simples em FormData", () => {
    const entity = {
      name: "Natan Almeida",
      age: 21,
      requiredFields: ["name"],
    };
    const formModel = new FormModel(entity);
    const formData = formModel.toFormData();
    const result = formDataToObject(formData);

    expect(result).toEqual({
      name: "Natan Almeida",
      age: "21",
    });
  });

  it("ignora valores undefined e null", () => {
    const entity = {
      name: "Natan Almeida",
      email: undefined,
      phone: null,
      requiredFields: ["name"],
    };
    const formModel = new FormModel(entity);
    const formData = formModel.toFormData();
    const result = formDataToObject(formData);

    expect(result).toEqual({
      name: "Natan Almeida",
    });
  });

  it("converte arrays em FormData com índices", () => {
    const entity = {
      tags: ["vue", "javascript"],
      name: "Test",
      requiredFields: ["name"],
    };
    const formModel = new FormModel(entity);
    const formData = formModel.toFormData();
    const result = formDataToObject(formData);

    expect(result).toEqual({
      "tags[0]": "vue",
      "tags[1]": "javascript",
      name: "Test",
    });
  });

  it("trata valores falsy corretamente (exceto null)", () => {
    const entity = {
      active: false,
      count: 0,
      name: "",
      requiredFields: ["name"],
    };
    const formModel = new FormModel(entity);
    const formData = formModel.toFormData();
    const result = formDataToObject(formData);

    expect(result).toEqual({
      active: "false",
      count: "0",
      name: "",
    });
  });

  it("retorna FormData vazio para entidade vazia", () => {
    const entity = { requiredFields: [] };
    const formModel = new FormModel(entity);
    const formData = formModel.toFormData();
    const result = formDataToObject(formData);

    expect(result).toEqual({});
  });
});

// ログイン画面 /login(決定 D-05「画面」。FR-001・FR-002・FR-021・FR-024。画面共通規則)。
// 社員番号・パスワードの欄と、ログインのボタンを縦に並べる。誤りの文はボタンの上に出す。
import { useRef, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import { useApi } from "@/api/ApiContext";
import { ApiError, UNEXPECTED_ERROR_MESSAGE } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const REQUIRED_MESSAGE = "入力してください";
const EMPLOYEE_NO_FORMAT_MESSAGE = "数字 6 桁で入れてください";
const EMPLOYEE_NO_PATTERN = /^[0-9]{6}$/;

type FieldErrors = { employeeNo?: string; password?: string };

/** 入力を確かめる。誤りが無ければ空のものを返す(画面共通規則の「共通の入力チェック」)。 */
export function validateLogin(employeeNo: string, password: string): FieldErrors {
  const errors: FieldErrors = {};
  if (employeeNo === "") {
    errors.employeeNo = REQUIRED_MESSAGE;
  } else if (!EMPLOYEE_NO_PATTERN.test(employeeNo)) {
    errors.employeeNo = EMPLOYEE_NO_FORMAT_MESSAGE;
  }
  if (password === "") {
    errors.password = REQUIRED_MESSAGE;
  }
  return errors;
}

export function LoginPage() {
  const api = useApi();
  const navigate = useNavigate();
  const [employeeNo, setEmployeeNo] = useState("");
  const [password, setPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  // 二重送信の防止: ボタンを押せなくするのに加え、描き直しの前の 2 回目の送信も止める
  const sending = useRef(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (sending.current) return;
    const errors = validateLogin(employeeNo, password);
    setFieldErrors(errors);
    if (errors.employeeNo !== undefined || errors.password !== undefined) {
      return;
    }
    sending.current = true;
    setSubmitting(true);
    setError(null);
    try {
      await api.login({ employee_no: employeeNo, password });
      await navigate("/menu", { replace: true });
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : UNEXPECTED_ERROR_MESSAGE);
    } finally {
      sending.current = false;
      setSubmitting(false);
    }
  }

  return (
    <main className="flex min-h-svh items-center justify-center p-4">
      <form noValidate onSubmit={handleSubmit} className="flex w-full max-w-sm flex-col gap-4">
        <h1 className="text-xl font-bold">ログイン</h1>
        <div className="flex flex-col gap-1">
          <Label htmlFor="employee-no">社員番号</Label>
          <Input
            id="employee-no"
            name="employee_no"
            inputMode="numeric"
            autoComplete="username"
            value={employeeNo}
            onChange={(event) => setEmployeeNo(event.target.value)}
            aria-invalid={fieldErrors.employeeNo !== undefined}
            aria-describedby={fieldErrors.employeeNo !== undefined ? "employee-no-error" : undefined}
          />
          {fieldErrors.employeeNo !== undefined && (
            <p id="employee-no-error" className="text-sm text-destructive">
              {fieldErrors.employeeNo}
            </p>
          )}
        </div>
        <div className="flex flex-col gap-1">
          <Label htmlFor="password">パスワード</Label>
          <Input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            aria-invalid={fieldErrors.password !== undefined}
            aria-describedby={fieldErrors.password !== undefined ? "password-error" : undefined}
          />
          {fieldErrors.password !== undefined && (
            <p id="password-error" className="text-sm text-destructive">
              {fieldErrors.password}
            </p>
          )}
        </div>
        {error !== null && (
          <p role="alert" className="text-sm text-destructive">
            {error}
          </p>
        )}
        <Button type="submit" disabled={submitting} className="w-full">
          ログイン
        </Button>
      </form>
    </main>
  );
}

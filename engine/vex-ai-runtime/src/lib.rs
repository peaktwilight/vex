use pyo3::prelude::*;

#[pyfunction]
fn runtime_info() -> Vec<(&'static str, &'static str)> {
    vec![
        ("name", "vex-ai-runtime"),
        ("engine", "onnxruntime-planned"),
        ("core_language", "rust"),
        ("status", "scaffold"),
    ]
}

#[pyfunction]
fn healthcheck() -> &'static str {
    "ok"
}

#[pymodule]
fn _core(_py: Python<'_>, module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(runtime_info, module)?)?;
    module.add_function(wrap_pyfunction!(healthcheck, module)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn runtime_info_contains_name() {
        let info = runtime_info();
        assert!(info
            .iter()
            .any(|(key, value)| *key == "name" && *value == "vex-ai-runtime"));
    }

    #[test]
    fn healthcheck_returns_ok() {
        assert_eq!(healthcheck(), "ok");
    }
}
